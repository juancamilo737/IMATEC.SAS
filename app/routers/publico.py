"""Sitio público: inicio, servicios, catálogo, ficha de producto, contacto y carrito."""
import json

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from .. import db
from ..auth import autenticar, current_user, es_staff, make_session
from ..config import SESSION_COOKIE, SESSION_MAX_AGE
from ..documentos import crear_pedido, pedido_completo

router = APIRouter()

IMG_SERVICIO = {
    "equipos-industriales": "productos/mesa-de-trabajo.jpg",
    "equipos-hospitalarios": "productos/lavamanos-quirurgico-doble.jpg",
    "estructuras-metalicas": "productos/estructuras-metalicas2.jpg",
    "obras-civiles": "productos/whatsapp-image-2021-04-12-at-4-12-18-pm.jpg",
    "extraccion-nucleos": "productos/tapas-de-acero-inoxidable-para-tanque-eq0.jpg",
}

SQL_PRODUCTO = """SELECT p.*, c.nombre AS categoria, c.slug AS categoria_slug
                  FROM productos p JOIN categorias c ON c.id=p.categoria_id"""


def materiales_de_grupo(prefijo: str) -> list:
    """Diámetros de una familia de tubería, con la existencia real de bodega,
    ordenados como en el Excel (1/4\" , 3/8\" , 1/2\" … 10\")."""
    if not prefijo:
        return []
    filas = db.q("""SELECT id, sku, diametro, descripcion, cantidad, unidad, precio_venta
                    FROM materiales
                    WHERE sku LIKE ? AND activo=1 AND publicado=1""", (prefijo + "%",))
    orden = {v: i for i, v in enumerate(db.opciones("diametro"))}
    filas.sort(key=lambda m: orden.get((m["diametro"] or "").strip(), 999))
    for m in filas:
        m["disponible"] = (m["cantidad"] or 0) > 0
    return filas


def conteo_grupo(prefijo: str) -> dict:
    if not prefijo:
        return {}
    return {
        "total": db.scalar("SELECT COUNT(*) FROM materiales WHERE sku LIKE ? AND activo=1 "
                           "AND publicado=1", (prefijo + "%",)),
        "disponibles": db.scalar("SELECT COUNT(*) FROM materiales WHERE sku LIKE ? AND activo=1 "
                                 "AND publicado=1 AND cantidad>0", (prefijo + "%",)),
    }


def _servicios() -> list:
    """Las 5 líneas de servicio que la empresa publica en su sitio."""
    slugs = ["equipos-industriales", "estructuras-metalicas", "equipos-hospitalarios",
             "obras-civiles", "extraccion-nucleos"]
    marcas = ",".join("?" * len(slugs))
    filas = db.q(f"SELECT * FROM categorias WHERE slug IN ({marcas})", slugs)
    por_slug = {f["slug"]: f for f in filas}
    salida = []
    for s in slugs:
        if s in por_slug:
            item = dict(por_slug[s])
            item["imagen"] = IMG_SERVICIO.get(s, "")
            salida.append(item)
    return salida


@router.get("/")
def inicio(request: Request):
    from ..main import render
    return render(request, "public/inicio.html",
                  pagina="inicio",
                  servicios=_servicios(),
                  destacados=db.q(f"{SQL_PRODUCTO} WHERE p.activo=1 AND p.destacado=1 "
                                  "ORDER BY c.orden, p.id LIMIT 6"),
                  familias=[dict(f, grupo=conteo_grupo(f["grupo_sku"]))
                            for f in db.q(f"{SQL_PRODUCTO} WHERE p.activo=1 "
                                          "AND p.grupo_sku<>'' ORDER BY p.id LIMIT 4")],
                  lineas=db.q("""SELECT c.slug, c.nombre, c.descripcion,
                                 COUNT(p.id) AS n FROM categorias c
                                 JOIN productos p ON p.categoria_id=c.id AND p.activo=1
                                 WHERE c.activo=1 AND c.orden >= 10
                                 GROUP BY c.id ORDER BY c.orden"""),
                  total_categorias=db.scalar(
                      "SELECT COUNT(DISTINCT categoria_id) FROM productos WHERE activo=1"),
                  total_productos=db.scalar("SELECT COUNT(*) FROM productos WHERE activo=1"))


@router.get("/servicios")
def servicios(request: Request):
    from ..main import render
    return render(request, "public/servicios.html", pagina="servicios", servicios=_servicios())


@router.get("/nosotros")
def nosotros(request: Request):
    from ..main import render
    return render(request, "public/nosotros.html", pagina="nosotros")


@router.get("/catalogo")
def catalogo(request: Request, cat: str = "", q: str = ""):
    from ..main import render
    sql, params = f"{SQL_PRODUCTO} WHERE p.activo=1", []
    if cat:
        sql += " AND c.slug=?"
        params.append(cat)
    if q:
        sql += " AND (p.nombre LIKE ? OR p.descripcion LIKE ? OR p.sku LIKE ? OR p.material LIKE ?)"
        params += [f"%{q}%"] * 4
    sql += " ORDER BY c.orden, p.destacado DESC, p.nombre"
    productos = db.q(sql, params)
    for pr in productos:
        pr["grupo"] = conteo_grupo(pr.get("grupo_sku") or "")
    return render(request, "public/catalogo.html", pagina="catalogo", cat=cat, q=q,
                  productos=productos,
                  categorias=db.q("SELECT * FROM categorias WHERE activo=1 ORDER BY orden"),
                  categoria_actual=db.q1("SELECT * FROM categorias WHERE slug=?", (cat,)) if cat else None)


@router.get("/producto/{slug}")
def producto(request: Request, slug: str):
    from ..main import render
    p = db.q1(f"{SQL_PRODUCTO} WHERE p.slug=? AND p.activo=1", (slug,))
    if not p:
        return RedirectResponse("/catalogo", status_code=303)
    return render(request, "public/producto.html", pagina="catalogo", p=p,
                  medidas=materiales_de_grupo(p.get("grupo_sku") or ""),
                  relacionados=[dict(r, grupo=conteo_grupo(r["grupo_sku"] or ""))
                                for r in db.q(f"{SQL_PRODUCTO} WHERE p.categoria_id=? AND p.id<>? "
                                              "AND p.activo=1 ORDER BY p.destacado DESC LIMIT 4",
                                              (p["categoria_id"], p["id"]))])


@router.get("/creditos")
def creditos(request: Request):
    """Atribución de las fotos de materiales (exigida por sus licencias Creative Commons)."""
    from ..main import render
    import json
    from ..config import STATIC_DIR
    ruta = STATIC_DIR / "img" / "materiales" / "creditos.json"
    datos = json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}
    return render(request, "public/creditos.html", pagina="creditos", creditos=datos)


@router.get("/contacto")
def contacto(request: Request, enviado: int = 0):
    from ..main import render
    return render(request, "public/contacto.html", pagina="contacto", enviado=bool(enviado))


@router.post("/contacto")
def contacto_enviar(request: Request, nombre: str = Form(...), mensaje: str = Form(...),
                    email: str = Form(""), telefono: str = Form("")):
    db.ex("INSERT INTO mensajes(nombre,email,telefono,mensaje) VALUES(?,?,?,?)",
          (nombre, email, telefono, mensaje))
    return RedirectResponse("/contacto?enviado=1", status_code=303)


@router.get("/carrito")
def carrito(request: Request):
    from ..main import render
    usuario = current_user(request)
    cliente = db.q1("SELECT * FROM clientes WHERE id=?", (usuario["cliente_id"],)) \
        if usuario and usuario.get("cliente_id") else None
    return render(request, "public/carrito.html", pagina="carrito", cliente=cliente)


@router.post("/carrito/enviar")
def carrito_enviar(request: Request, items_json: str = Form(...),
                   nombre_contacto: str = Form(...), email: str = Form(...),
                   telefono: str = Form(...), empresa: str = Form(""), notas: str = Form("")):
    from ..main import render
    usuario = current_user(request)
    try:
        crudos = json.loads(items_json or "[]")
    except json.JSONDecodeError:
        crudos = []
    if not crudos:
        return RedirectResponse("/carrito", status_code=303)

    items = []
    for it in crudos:
        ident = str(it.get("id") or "")
        producto = material = None
        if ident.startswith("m"):          # material del inventario: "m123"
            material = db.q1("SELECT * FROM materiales WHERE id=? AND activo=1", (ident[1:],))
        elif ident:
            producto = db.q1("SELECT * FROM productos WHERE id=?", (ident,))

        if material:
            descripcion = f"{material['descripcion']} ({material['sku']})"
            unidad = material["unidad"] or "Metros"
            precio = float(material["precio_venta"] or 0)
        elif producto:
            descripcion = producto["nombre"]
            unidad = producto["unidad"] or "UND"
            precio = float(producto["precio"] or 0)
        else:
            descripcion = str(it.get("nombre", "Producto"))[:200]
            unidad = it.get("unidad") or "UND"
            precio = 0.0

        items.append({
            "producto_id": producto["id"] if producto else None,
            "material_id": material["id"] if material else None,
            "descripcion": descripcion,
            "cantidad": max(float(it.get("cantidad") or 1), 0.01),
            "unidad": unidad,
            "precio": precio,
            "observacion": str(it.get("observacion", ""))[:500],
        })
    pid = crear_pedido(items, nombre_contacto=nombre_contacto, email=email, telefono=telefono,
                       empresa=empresa, notas=notas,
                       cliente_id=usuario.get("cliente_id") if usuario else None)
    return render(request, "public/pedido_ok.html", pagina="carrito", pedido=pedido_completo(pid))


# ------------------------------------------------------------------ sesión
@router.get("/acceso")
def acceso(request: Request, destino: str = "", mensaje: str = ""):
    from ..main import render
    usuario = current_user(request)
    if usuario:
        return RedirectResponse("/admin" if es_staff(usuario) else "/portal", status_code=303)
    return render(request, "public/acceso.html", destino=destino, mensaje=mensaje, error=None)


@router.post("/acceso")
def acceso_enviar(request: Request, email: str = Form(...), password: str = Form(...),
                  destino: str = Form("")):
    from ..main import render
    u = autenticar(email, password)
    if not u:
        return render(request, "public/acceso.html", destino=destino,
                      error="Correo o contraseña incorrectos. Verifique e intente de nuevo.")
    ruta = destino or ("/admin" if u["rol"] in ("admin", "vendedor") else "/portal")
    resp = RedirectResponse(ruta, status_code=303)
    resp.set_cookie(SESSION_COOKIE, make_session(dict(u)), max_age=SESSION_MAX_AGE,
                    httponly=True, samesite="lax")
    return resp


@router.get("/salir")
def salir():
    resp = RedirectResponse("/", status_code=303)
    resp.delete_cookie(SESSION_COOKIE)
    return resp
