"""Portal del cliente: sus solicitudes, cotizaciones, remisiones y facturas."""
from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from .. import db, documentos as D
from ..auth import current_user, hash_password, verify_password

router = APIRouter(prefix="/portal")


def _guard(request: Request):
    """Sólo clientes con perfil asociado."""
    u = current_user(request)
    if not u:
        return None, None, RedirectResponse(f"/acceso?destino={request.url.path}", status_code=303)
    if u.get("rol") in ("admin", "vendedor"):
        return None, None, RedirectResponse("/admin", status_code=303)
    cli = db.q1("SELECT * FROM clientes WHERE id=?", (u.get("cliente_id"),)) \
        if u.get("cliente_id") else None
    if not cli:
        return None, None, RedirectResponse("/?sin_perfil=1", status_code=303)
    return u, cli, None


def _mio(tabla: str, cid: int, extra: str = "", limite: int = 200) -> list:
    return db.q(f"SELECT * FROM {tabla} WHERE cliente_id=? {extra} ORDER BY id DESC LIMIT {limite}",
                (cid,))


@router.get("")
@router.get("/")
def inicio(request: Request, aviso: str = "", tipo: str = "ok"):
    from ..main import render
    u, cli, r = _guard(request)
    if r:
        return r
    return render(request, "portal/inicio.html", seccion="inicio", cliente=cli,
        aviso=aviso, aviso_tipo=tipo,
        saldo=db.scalar("SELECT COALESCE(SUM(saldo),0) FROM facturas WHERE cliente_id=? "
                        "AND estado NOT IN ('anulada','borrador')", (cli["id"],)),
        vencidas=db.scalar("SELECT COUNT(*) FROM facturas WHERE cliente_id=? AND saldo>0 "
                           "AND fecha_vencimiento<date('now','localtime') "
                           "AND estado NOT IN ('anulada','borrador','pagada')", (cli["id"],)),
        n_cot=db.scalar("SELECT COUNT(*) FROM cotizaciones WHERE cliente_id=? "
                        "AND estado IN ('enviada','borrador')", (cli["id"],)),
        en_camino=db.scalar("SELECT COUNT(*) FROM remisiones WHERE cliente_id=? "
                            "AND estado IN ('pendiente','despachada')", (cli["id"],)),
        cotizaciones=_mio("cotizaciones", cli["id"], "AND estado<>'borrador'", 5),
        remisiones=_mio("remisiones", cli["id"], "", 5),
        facturas=_mio("facturas", cli["id"], "AND estado<>'borrador'", 5),
        solicitudes=_mio("pedidos", cli["id"], "", 5))


@router.get("/solicitudes")
def solicitudes(request: Request):
    from ..main import render
    u, cli, r = _guard(request)
    if r:
        return r
    filas = _mio("pedidos", cli["id"])
    for p in filas:
        p["items"] = db.q("SELECT * FROM pedido_items WHERE pedido_id=?", (p["id"],))
    return render(request, "portal/solicitudes.html", seccion="pedidos", cliente=cli, pedidos=filas)


@router.get("/cotizaciones")
def cotizaciones(request: Request, aviso: str = "", tipo: str = "ok"):
    from ..main import render
    u, cli, r = _guard(request)
    if r:
        return r
    return render(request, "portal/lista.html", seccion="cotizaciones", cliente=cli,
        aviso=aviso, aviso_tipo=tipo, clase="cotizaciones",
        titulo="Mis cotizaciones",
        filas=db.q("""SELECT *, date(fecha,'+'||validez_dias||' day') AS vence
                      FROM cotizaciones WHERE cliente_id=? AND estado<>'borrador'
                      ORDER BY id DESC""", (cli["id"],)))


@router.get("/remisiones")
def remisiones(request: Request):
    from ..main import render
    u, cli, r = _guard(request)
    if r:
        return r
    return render(request, "portal/lista.html", seccion="remisiones", cliente=cli,
                  clase="remisiones", titulo="Mis remisiones",
                  filas=_mio("remisiones", cli["id"]))


@router.get("/facturas")
def facturas(request: Request):
    from ..main import render
    u, cli, r = _guard(request)
    if r:
        return r
    return render(request, "portal/lista.html", seccion="facturas", cliente=cli,
                  clase="facturas", titulo="Mis facturas",
                  filas=_mio("facturas", cli["id"], "AND estado<>'borrador'"))


@router.get("/cotizaciones/{cid}")
def cotizacion(request: Request, cid: int):
    from ..main import render
    u, cli, r = _guard(request)
    if r:
        return r
    c = D.cotizacion_completa(cid)
    if not c or c["cliente_id"] != cli["id"] or c["estado"] == "borrador":
        return RedirectResponse("/portal/cotizaciones", status_code=303)
    return render(request, "docs/cotizacion.html", seccion="cotizaciones", c=c,
                  panel=False, portal=True, cliente=cli)


@router.post("/cotizaciones/responder")
def cotizacion_responder(request: Request, cotizacion_id: int = Form(...),
                         decision: str = Form(...)):
    u, cli, r = _guard(request)
    if r:
        return r
    c = db.q1("SELECT * FROM cotizaciones WHERE id=?", (cotizacion_id,))
    if not c or c["cliente_id"] != cli["id"]:
        return RedirectResponse("/portal/cotizaciones", status_code=303)
    estado = "aprobada" if decision == "aprobar" else "rechazada"
    D.cambiar_estado_cotizacion(cotizacion_id, estado, u["email"])
    texto = ("¡Gracias! Aprobó la cotización " + c["numero"] +
             ". Nuestro equipo se comunica con usted para coordinar la fabricación."
             if estado == "aprobada"
             else f"Registramos que la cotización {c['numero']} no fue aprobada.")
    return RedirectResponse(f"/portal/cotizaciones?aviso={texto}", status_code=303)


@router.get("/remisiones/{rid}")
def remision(request: Request, rid: int):
    from ..main import render
    u, cli, r = _guard(request)
    if r:
        return r
    rem = D.remision_completa(rid)
    if not rem or rem["cliente_id"] != cli["id"]:
        return RedirectResponse("/portal/remisiones", status_code=303)
    return render(request, "docs/remision.html", seccion="remisiones", r=rem,
                  panel=False, portal=True, cliente=cli)


@router.get("/facturas/{fid}")
def factura(request: Request, fid: int):
    from ..main import render
    u, cli, r = _guard(request)
    if r:
        return r
    f = D.factura_completa(fid)
    if not f or f["cliente_id"] != cli["id"] or f["estado"] == "borrador":
        return RedirectResponse("/portal/facturas", status_code=303)
    return render(request, "docs/factura.html", seccion="facturas", f=f,
                  panel=False, portal=True, cliente=cli, dian_lista=False)


@router.get("/perfil")
def perfil(request: Request, aviso: str = "", tipo: str = "ok"):
    from ..main import render
    u, cli, r = _guard(request)
    if r:
        return r
    return render(request, "portal/perfil.html", seccion="perfil", cliente=cli,
                  aviso=aviso, aviso_tipo=tipo)


@router.post("/perfil/guardar")
def perfil_guardar(request: Request, contacto: str = Form(""), email: str = Form(""),
                   telefono: str = Form(""), direccion: str = Form(""), ciudad: str = Form("")):
    u, cli, r = _guard(request)
    if r:
        return r
    db.ex("""UPDATE clientes SET contacto=?,email=?,telefono=?,direccion=?,ciudad=? WHERE id=?""",
          (contacto, email, telefono, direccion, ciudad, cli["id"]))
    db.log(u["email"], "actualizar", "perfil", cli["razon_social"])
    return RedirectResponse("/portal/perfil?aviso=Sus datos fueron actualizados.", status_code=303)


@router.post("/perfil/clave")
def perfil_clave(request: Request, actual: str = Form(...), nueva: str = Form(...),
                 confirmar: str = Form(...)):
    u, cli, r = _guard(request)
    if r:
        return r
    row = db.q1("SELECT password_hash FROM usuarios WHERE id=?", (u["uid"],))
    if not row or not verify_password(actual, row["password_hash"]):
        return RedirectResponse("/portal/perfil?aviso=La contraseña actual no es correcta.&tipo=error",
                                status_code=303)
    if nueva != confirmar or len(nueva) < 6:
        return RedirectResponse("/portal/perfil?aviso=La nueva contraseña no coincide o es muy "
                                "corta (mínimo 6 caracteres).&tipo=error", status_code=303)
    db.ex("UPDATE usuarios SET password_hash=? WHERE id=?", (hash_password(nueva), u["uid"]))
    return RedirectResponse("/portal/perfil?aviso=Su contraseña fue actualizada.", status_code=303)
