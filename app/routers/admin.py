"""Panel de gestión: inventario, despachos, cotizaciones, remisiones y facturas."""
import json
import shutil
from datetime import date, datetime

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse

from .. import db, documentos as D, excel_sync
from ..auth import crear_usuario, current_user, es_staff, hash_password
from ..config import DB_PATH, IMAGENES_DIR, UPLOAD_DIR
from ..db import estado_material
from ..utils import slugify

router = APIRouter(prefix="/admin")


def _guard(request: Request):
    """Devuelve el usuario si es del equipo IMATEC; si no, a la pantalla de acceso."""
    u = current_user(request)
    if not es_staff(u):
        return None, RedirectResponse(f"/acceso?destino={request.url.path}", status_code=303)
    return u, None


def _volver(ruta: str, aviso: str = "", tipo: str = "ok"):
    sep = "&" if "?" in ruta else "?"
    extra = f"{sep}aviso={aviso}&tipo={tipo}" if aviso else ""
    return RedirectResponse(f"{ruta}{extra}", status_code=303)


def _items_de_form(items_json: str) -> list:
    try:
        crudos = json.loads(items_json or "[]")
    except json.JSONDecodeError:
        return []
    items = []
    for it in crudos:
        desc = str(it.get("descripcion", "")).strip()
        if not desc:
            continue
        items.append({
            "producto_id": it.get("producto_id") or None,
            "descripcion": desc,
            "especificaciones": str(it.get("especificaciones", ""))[:800],
            "cantidad": float(it.get("cantidad") or 0),
            "unidad": it.get("unidad") or "UND",
            "precio": float(it.get("precio") or 0),
            "descuento_pct": float(it.get("descuento_pct") or 0),
            "iva_pct": float(it.get("iva_pct") or 0),
            "observacion": str(it.get("observacion", ""))[:500],
        })
    return items


# =====================================================================
#  DASHBOARD
# =====================================================================
@router.get("")
@router.get("/")
def inicio(request: Request, aviso: str = "", tipo: str = "ok"):
    from ..main import render
    u, r = _guard(request)
    if r:
        return r
    kpis = {
        "pedidos_nuevos": db.scalar("SELECT COUNT(*) FROM pedidos WHERE estado='nuevo'"),
        "cot_abiertas": db.scalar(
            "SELECT COUNT(*) FROM cotizaciones WHERE estado IN ('borrador','enviada')"),
        "cot_valor": db.scalar(
            "SELECT COALESCE(SUM(total),0) FROM cotizaciones WHERE estado IN ('borrador','enviada')"),
        "por_despachar": db.scalar("SELECT COUNT(*) FROM remisiones WHERE estado='pendiente'"),
        "cartera": db.scalar("SELECT COALESCE(SUM(saldo),0) FROM facturas "
                             "WHERE estado NOT IN ('anulada','borrador','pagada')"),
        "vencidas": db.scalar("SELECT COUNT(*) FROM facturas WHERE saldo>0 "
                              "AND estado NOT IN ('anulada','borrador','pagada') "
                              "AND fecha_vencimiento < date('now','localtime')"),
        "facturado_mes": db.scalar(
            "SELECT COALESCE(SUM(total),0) FROM facturas WHERE estado NOT IN ('anulada','borrador') "
            "AND strftime('%Y-%m',fecha_emision)=strftime('%Y-%m','now','localtime')"),
        "materiales": db.scalar("SELECT COUNT(*) FROM materiales WHERE activo=1"),
        "agotados": db.scalar("SELECT COUNT(*) FROM materiales WHERE activo=1 AND cantidad<=0"),
        "bajo_min": db.scalar("SELECT COUNT(*) FROM materiales WHERE activo=1 "
                              "AND cantidad>0 AND cantidad<=stock_minimo"),
        "clientes": db.scalar("SELECT COUNT(*) FROM clientes WHERE activo=1"),
    }
    return render(request, "admin/inicio.html", seccion="inicio", aviso=aviso, aviso_tipo=tipo,
        k=kpis,
        pedidos=db.q("SELECT * FROM pedidos WHERE estado='nuevo' ORDER BY id DESC LIMIT 6"),
        cotizaciones=db.q("""SELECT co.*, cl.razon_social FROM cotizaciones co
                             JOIN clientes cl ON cl.id=co.cliente_id
                             ORDER BY co.id DESC LIMIT 6"""),
        despachos=db.q("""SELECT re.*, cl.razon_social FROM remisiones re
                          JOIN clientes cl ON cl.id=re.cliente_id
                          WHERE re.estado IN ('pendiente','despachada')
                          ORDER BY re.id DESC LIMIT 6"""),
        cartera=db.q("""SELECT fa.*, cl.razon_social FROM facturas fa
                        JOIN clientes cl ON cl.id=fa.cliente_id
                        WHERE fa.saldo>0 AND fa.estado NOT IN ('anulada','borrador','pagada')
                        ORDER BY fa.fecha_vencimiento LIMIT 6"""),
        alertas=db.q("""SELECT * FROM materiales WHERE activo=1 AND cantidad<=stock_minimo
                        ORDER BY cantidad LIMIT 8"""))


# =====================================================================
#  INVENTARIO DE MATERIALES  (el Excel de IMATEC, ahora editable)
# =====================================================================
@router.get("/inventario")
def inventario(request: Request, q: str = "", categoria: str = "", material: str = "",
               estado: str = "", aviso: str = "", tipo: str = "ok"):
    from ..main import render
    u, r = _guard(request)
    if r:
        return r
    sql, params = "SELECT * FROM materiales WHERE activo=1", []
    if q:
        sql += " AND (sku LIKE ? OR descripcion LIKE ? OR notas LIKE ?)"
        params += [f"%{q}%"] * 3
    if categoria:
        sql += " AND categoria=?"
        params.append(categoria)
    if material:
        sql += " AND material=?"
        params.append(material)
    if estado == "disponible":
        sql += " AND cantidad>0"
    elif estado == "agotado":
        sql += " AND cantidad<=0"
    elif estado == "bajo":
        sql += " AND cantidad<=stock_minimo"
    sql += " ORDER BY categoria, material, sku"
    filas = db.q(sql, params)
    for f in filas:
        f["estado"] = estado_material(f["cantidad"])
    return render(request, "admin/inventario.html", seccion="inventario",
                  aviso=aviso, aviso_tipo=tipo, materiales=filas,
                  q=q, categoria=categoria, material=material, estado=estado,
                  cats=db.opciones("categoria"), mats=db.opciones("material"),
                  diams=db.opciones("diametro"), unidades=db.opciones("unidad"),
                  total=db.scalar("SELECT COUNT(*) FROM materiales WHERE activo=1"))


@router.post("/inventario/guardar")
def inventario_guardar(request: Request, sku: str = Form(...), descripcion: str = Form(...),
                       categoria: str = Form("Otros"), material: str = Form(""),
                       diametro: str = Form(""), cantidad: float = Form(0),
                       unidad: str = Form("Unidades"), notas: str = Form(""),
                       stock_minimo: float = Form(0), ubicacion: str = Form(""),
                       costo_unitario: float = Form(0), proveedor: str = Form(""),
                       precio_venta: float = Form(0), publicado: str = Form(""),
                       material_id: str = Form("")):
    u, r = _guard(request)
    if r:
        return r
    sku = sku.strip()
    for lista, valor in (("categoria", categoria), ("material", material),
                         ("diametro", diametro), ("unidad", unidad)):
        if valor.strip():
            db.ex("INSERT OR IGNORE INTO listas(lista,valor,orden) VALUES(?,?,99)",
                  (lista, valor.strip()))

    if material_id:  # edición
        anterior = db.q1("SELECT * FROM materiales WHERE id=?", (material_id,))
        if not anterior:
            return _volver("/admin/inventario", "No se encontró el ítem.", "error")
        db.ex("""UPDATE materiales SET sku=?,categoria=?,material=?,diametro=?,descripcion=?,
                 cantidad=?,unidad=?,notas=?,stock_minimo=?,ubicacion=?,costo_unitario=?,
                 proveedor=?,precio_venta=?,publicado=?,
                 actualizado_en=datetime('now','localtime') WHERE id=?""",
              (sku, categoria, material, diametro, descripcion, cantidad, unidad, notas,
               stock_minimo, ubicacion or "Bodega principal", costo_unitario, proveedor,
               precio_venta, 1 if publicado else 0, material_id))
        delta = float(cantidad) - float(anterior["cantidad"] or 0)
        if abs(delta) > 1e-9:
            excel_sync._mov(material_id, "ajuste", delta, cantidad,
                            "Ajuste manual desde el panel", u["email"])
        db.log(u["email"], "actualizar", "material", sku)
        aviso = f"Ítem <strong>{sku}</strong> actualizado."
    else:  # alta
        if db.q1("SELECT 1 FROM materiales WHERE sku=?", (sku,)):
            return _volver("/admin/inventario", f"Ya existe un ítem con el ID {sku}.", "error")
        mid = db.ex("""INSERT INTO materiales
                       (sku,categoria,material,diametro,descripcion,cantidad,unidad,notas,
                        stock_minimo,ubicacion,costo_unitario,proveedor,precio_venta,publicado)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (sku, categoria, material, diametro, descripcion, cantidad, unidad, notas,
                     stock_minimo, ubicacion or "Bodega principal", costo_unitario, proveedor,
                     precio_venta, 1 if publicado else 0))
        if cantidad:
            excel_sync._mov(mid, "entrada", cantidad, cantidad, "Saldo inicial", u["email"])
        db.log(u["email"], "crear", "material", sku)
        aviso = f"Ítem <strong>{sku}</strong> agregado al inventario."
    from ..seed import sembrar_materiales_en_catalogo
    sembrar_materiales_en_catalogo()
    excel_sync.exportar_control()
    return _volver("/admin/inventario", aviso)


@router.post("/inventario/movimiento")
def inventario_movimiento(request: Request, material_id: int = Form(...),
                          tipo: str = Form(...), cantidad: float = Form(...),
                          motivo: str = Form(""), documento: str = Form("")):
    u, r = _guard(request)
    if r:
        return r
    m = db.q1("SELECT * FROM materiales WHERE id=?", (material_id,))
    if not m:
        return _volver("/admin/inventario", "No se encontró el ítem.", "error")
    cant = abs(float(cantidad))
    if tipo == "salida":
        cant = -cant
    elif tipo == "ajuste":
        cant = float(cantidad) - float(m["cantidad"] or 0)
    saldo = round(float(m["cantidad"] or 0) + cant, 4)
    if saldo < 0:
        return _volver("/admin/inventario",
                       f"No hay saldo suficiente de <strong>{m['sku']}</strong>: "
                       f"disponible {m['cantidad']} {m['unidad']}.", "error")
    db.ex("UPDATE materiales SET cantidad=?, actualizado_en=datetime('now','localtime') WHERE id=?",
          (saldo, material_id))
    excel_sync._mov(material_id, tipo, cant, saldo, motivo, u["email"], documento)
    excel_sync.exportar_control()
    return _volver("/admin/inventario",
                   f"Movimiento registrado. Saldo de <strong>{m['sku']}</strong>: "
                   f"{saldo:g} {m['unidad']}.")


@router.post("/inventario/eliminar")
def inventario_eliminar(request: Request, material_id: int = Form(...)):
    u, r = _guard(request)
    if r:
        return r
    m = db.q1("SELECT sku FROM materiales WHERE id=?", (material_id,))
    db.ex("UPDATE materiales SET activo=0 WHERE id=?", (material_id,))
    db.log(u["email"], "eliminar", "material", m["sku"] if m else str(material_id))
    excel_sync.exportar_control()
    return _volver("/admin/inventario", f"Ítem {m['sku'] if m else ''} retirado del inventario.")


@router.post("/inventario/importar")
def inventario_importar(request: Request, archivo: UploadFile = File(...)):
    u, r = _guard(request)
    if r:
        return r
    destino = UPLOAD_DIR / f"import_{datetime.now():%Y%m%d_%H%M%S}_{archivo.filename}"
    with destino.open("wb") as f:
        shutil.copyfileobj(archivo.file, f)
    res = excel_sync.importar_inventario(destino, u["email"])
    if res.get("error"):
        return _volver("/admin/inventario", res["error"], "error")
    from ..seed import sembrar_materiales_en_catalogo
    sembrar_materiales_en_catalogo()
    excel_sync.exportar_control()
    return _volver("/admin/inventario",
                   f"Importación lista: <strong>{res['nuevos']}</strong> ítems nuevos y "
                   f"<strong>{res['actualizados']}</strong> actualizados.")


@router.post("/importar/{tipo}")
def importar_archivo(request: Request, tipo: str, archivo: UploadFile = File(...)):
    """Carga en producción los archivos que la empresa ya tiene:
    clientes exportados de Xubio, listado de precios y relación de cartera."""
    u, r = _guard(request)
    if r:
        return r
    destino = UPLOAD_DIR / f"{tipo}_{datetime.now():%Y%m%d_%H%M%S}_{archivo.filename}"
    with destino.open("wb") as f:
        shutil.copyfileobj(archivo.file, f)

    try:
        if tipo == "clientes":
            from ..importar_xubio import importar_clientes
            res = importar_clientes(destino, u["email"])
            aviso = (f"Clientes: <strong>{res['nuevos']}</strong> nuevos, "
                     f"<strong>{res['actualizados']}</strong> actualizados.")
        elif tipo == "precios":
            from ..importar_precios import importar_precios
            res = importar_precios(destino, u["email"])
            aviso = (f"Listado de precios: <strong>{res['nuevos']}</strong> productos nuevos y "
                     f"<strong>{res['actualizados']}</strong> actualizados. "
                     f"Quedan <strong>sin publicar</strong> hasta que confirme que esos "
                     f"valores son de venta (revíselos en Inventario).")
        elif tipo == "items":
            from ..importar_items import importar_items
            res = importar_items(destino, u["email"])
            aviso = (f"Histórico de cotizaciones: <strong>{res['nuevos']}</strong> productos "
                     f"nuevos y <strong>{res['actualizados']}</strong> actualizados. "
                     f"<strong>{res['publicados']}</strong> quedaron publicados (los cotizados "
                     f"dos veces o más). Precios tomados de lo realmente cotizado.")
        elif tipo == "cartera":
            from ..importar_cartera import importar_cartera
            res = importar_cartera(destino, u["email"])
            nuevos = res.get("clientes_creados", 0)
            aviso = (f"Cartera: <strong>{res['creadas']}</strong> facturas por "
                     f"<strong>{res['total']:,.0f}</strong>."
                     + (f" Se crearon {nuevos} cliente(s) que no estaban en Xubio; "
                        "complete sus datos." if nuevos else ""))
        else:
            return _volver("/admin/excel", "Tipo de archivo no reconocido.", "error")
    except Exception as e:
        return _volver("/admin/excel", f"No se pudo importar: {e}", "error")

    excel_sync.exportar_control()
    return _volver("/admin/excel", aviso)


@router.get("/kardex")
def kardex(request: Request, material_id: str = ""):
    from ..main import render
    u, r = _guard(request)
    if r:
        return r
    sql = """SELECT mm.*, ma.sku, ma.descripcion, ma.unidad FROM movimientos_material mm
             JOIN materiales ma ON ma.id=mm.material_id"""
    params = []
    if material_id:
        sql += " WHERE mm.material_id=?"
        params.append(material_id)
    sql += " ORDER BY mm.id DESC LIMIT 400"
    return render(request, "admin/kardex.html", seccion="kardex",
                  movimientos=db.q(sql, params), material_id=material_id,
                  materiales=db.q("SELECT id,sku,descripcion FROM materiales "
                                  "WHERE activo=1 ORDER BY sku"))


# =====================================================================
#  CLIENTES
# =====================================================================
@router.get("/clientes")
def clientes(request: Request, q: str = "", aviso: str = "", tipo: str = "ok"):
    from ..main import render
    u, r = _guard(request)
    if r:
        return r
    sql, params = "SELECT * FROM clientes WHERE 1=1", []
    if q:
        sql += " AND (razon_social LIKE ? OR documento LIKE ? OR contacto LIKE ? OR email LIKE ?)"
        params += [f"%{q}%"] * 4
    sql += " ORDER BY razon_social"
    filas = db.q(sql, params)
    for c in filas:
        c["saldo"] = db.scalar("SELECT COALESCE(SUM(saldo),0) FROM facturas WHERE cliente_id=? "
                               "AND estado NOT IN ('anulada','borrador')", (c["id"],))
        c["tiene_acceso"] = bool(db.q1("SELECT 1 FROM usuarios WHERE cliente_id=?", (c["id"],)))
    return render(request, "admin/clientes.html", seccion="clientes", clientes=filas, q=q,
                  aviso=aviso, aviso_tipo=tipo)


@router.post("/clientes/guardar")
def clientes_guardar(request: Request, razon_social: str = Form(...), documento: str = Form(...),
                     tipo_documento: str = Form("NIT"), dv: str = Form(""),
                     nombre_comercial: str = Form(""), contacto: str = Form(""),
                     email: str = Form(""), telefono: str = Form(""), direccion: str = Form(""),
                     ciudad: str = Form("Cali"), departamento: str = Form("Valle del Cauca"),
                     regimen: str = Form("Responsable de IVA"),
                     responsabilidad_fiscal: str = Form("O-1"), condicion_pago: int = Form(30),
                     cupo_credito: float = Form(0), descuento_pct: float = Form(0),
                     notas: str = Form(""), cliente_id: str = Form(""),
                     crear_acceso: str = Form(""), password: str = Form("")):
    u, r = _guard(request)
    if r:
        return r
    datos = (tipo_documento, documento.strip(), dv, razon_social.strip(), nombre_comercial,
             contacto, email.strip().lower(), telefono, direccion, ciudad, departamento,
             regimen, responsabilidad_fiscal, condicion_pago, cupo_credito, descuento_pct, notas)
    if cliente_id:
        db.ex("""UPDATE clientes SET tipo_documento=?,documento=?,dv=?,razon_social=?,
                 nombre_comercial=?,contacto=?,email=?,telefono=?,direccion=?,ciudad=?,
                 departamento=?,regimen=?,responsabilidad_fiscal=?,condicion_pago=?,
                 cupo_credito=?,descuento_pct=?,notas=? WHERE id=?""", (*datos, cliente_id))
        cid, aviso = int(cliente_id), f"Cliente <strong>{razon_social}</strong> actualizado."
    else:
        n = db.scalar("SELECT COUNT(*) FROM clientes") + 1
        cid = db.ex("""INSERT INTO clientes(codigo,tipo_documento,documento,dv,razon_social,
                       nombre_comercial,contacto,email,telefono,direccion,ciudad,departamento,
                       regimen,responsabilidad_fiscal,condicion_pago,cupo_credito,descuento_pct,notas)
                       VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (f"CL-{n:04d}", *datos))
        aviso = f"Cliente <strong>{razon_social}</strong> registrado."
    db.log(u["email"], "guardar", "cliente", razon_social)

    if crear_acceso and email:
        if db.q1("SELECT 1 FROM usuarios WHERE lower(email)=lower(?)", (email,)):
            aviso += " (Ya existía un usuario con ese correo, no se creó otro.)"
        else:
            clave = password.strip() or "Imatec2026*"
            crear_usuario(email, clave, contacto or razon_social, "cliente", cid)
            aviso += (f" Se creó su acceso al portal con el correo <strong>{email}</strong>"
                      f" y la contraseña <strong>{clave}</strong>.")
    excel_sync.exportar_control()
    return _volver("/admin/clientes", aviso)


@router.get("/clientes/{cid}")
def cliente_detalle(request: Request, cid: int):
    from ..main import render
    u, r = _guard(request)
    if r:
        return r
    c = db.q1("SELECT * FROM clientes WHERE id=?", (cid,))
    if not c:
        return _volver("/admin/clientes", "Cliente no encontrado.", "error")
    return render(request, "admin/cliente_detalle.html", seccion="clientes", c=c,
        usuarios=db.q("SELECT * FROM usuarios WHERE cliente_id=?", (cid,)),
        cotizaciones=db.q("SELECT * FROM cotizaciones WHERE cliente_id=? ORDER BY id DESC", (cid,)),
        remisiones=db.q("SELECT * FROM remisiones WHERE cliente_id=? ORDER BY id DESC", (cid,)),
        facturas=db.q("SELECT * FROM facturas WHERE cliente_id=? ORDER BY id DESC", (cid,)),
        saldo=db.scalar("SELECT COALESCE(SUM(saldo),0) FROM facturas WHERE cliente_id=? "
                        "AND estado NOT IN ('anulada','borrador')", (cid,)),
        comprado=db.scalar("SELECT COALESCE(SUM(total),0) FROM facturas WHERE cliente_id=? "
                           "AND estado NOT IN ('anulada','borrador')", (cid,)))


# =====================================================================
#  SOLICITUDES WEB (pedidos)
# =====================================================================
@router.get("/pedidos")
def pedidos(request: Request, estado: str = "", aviso: str = "", tipo: str = "ok"):
    from ..main import render
    u, r = _guard(request)
    if r:
        return r
    sql, params = "SELECT * FROM pedidos WHERE 1=1", []
    if estado:
        sql += " AND estado=?"
        params.append(estado)
    sql += " ORDER BY id DESC LIMIT 200"
    filas = db.q(sql, params)
    for p in filas:
        p["items"] = db.q("SELECT * FROM pedido_items WHERE pedido_id=?", (p["id"],))
    return render(request, "admin/pedidos.html", seccion="pedidos", pedidos=filas,
                  estado=estado, aviso=aviso, aviso_tipo=tipo,
                  clientes=db.q("SELECT id,razon_social,documento FROM clientes "
                                "WHERE activo=1 ORDER BY razon_social"))


@router.post("/pedidos/cotizar")
def pedido_cotizar(request: Request, pedido_id: int = Form(...), cliente_id: int = Form(...)):
    u, r = _guard(request)
    if r:
        return r
    cid = D.pedido_a_cotizacion(pedido_id, cliente_id, u["email"])
    return RedirectResponse(f"/admin/cotizaciones/{cid}/editar", status_code=303)


@router.post("/pedidos/estado")
def pedido_estado(request: Request, pedido_id: int = Form(...), estado: str = Form(...)):
    u, r = _guard(request)
    if r:
        return r
    db.ex("UPDATE pedidos SET estado=? WHERE id=?", (estado, pedido_id))
    db.log(u["email"], "estado", "pedido", str(pedido_id), estado)
    return _volver("/admin/pedidos", "Solicitud actualizada.")


# =====================================================================
#  COTIZACIONES
# =====================================================================
@router.get("/cotizaciones")
def cotizaciones(request: Request, estado: str = "", q: str = "", aviso: str = "", tipo: str = "ok"):
    from ..main import render
    u, r = _guard(request)
    if r:
        return r
    sql = """SELECT co.*, cl.razon_social, date(co.fecha,'+'||co.validez_dias||' day') AS vence
             FROM cotizaciones co JOIN clientes cl ON cl.id=co.cliente_id WHERE 1=1"""
    params = []
    if estado:
        sql += " AND co.estado=?"
        params.append(estado)
    if q:
        sql += " AND (co.numero LIKE ? OR cl.razon_social LIKE ?)"
        params += [f"%{q}%"] * 2
    sql += " ORDER BY co.id DESC LIMIT 300"
    return render(request, "admin/cotizaciones.html", seccion="cotizaciones",
                  cotizaciones=db.q(sql, params), estado=estado, q=q,
                  aviso=aviso, aviso_tipo=tipo)


@router.get("/cotizaciones/nueva")
def cotizacion_nueva(request: Request, cliente_id: str = ""):
    from ..main import render
    u, r = _guard(request)
    if r:
        return r
    return render(request, "admin/cotizacion_editar.html", seccion="cotizaciones", c=None,
                  cliente_id=cliente_id, **_datos_editor())


@router.get("/cotizaciones/{cid}/editar")
def cotizacion_editar(request: Request, cid: int):
    from ..main import render
    u, r = _guard(request)
    if r:
        return r
    c = D.cotizacion_completa(cid)
    if not c:
        return _volver("/admin/cotizaciones", "Cotización no encontrada.", "error")
    return render(request, "admin/cotizacion_editar.html", seccion="cotizaciones", c=c,
                  cliente_id=c["cliente_id"], **_datos_editor())


def _datos_editor() -> dict:
    return {
        "clientes": db.q("SELECT id,razon_social,documento,condicion_pago,descuento_pct "
                         "FROM clientes WHERE activo=1 ORDER BY razon_social"),
        "productos": db.q("""SELECT p.id,p.sku,p.nombre,p.precio,p.unidad,p.iva_pct,
                             p.especificaciones, c.nombre AS categoria FROM productos p
                             JOIN categorias c ON c.id=p.categoria_id
                             WHERE p.activo=1 ORDER BY c.orden, p.nombre"""),
        "iva_defecto": float(db.empresa().get("iva_defecto") or 19),
    }


@router.post("/cotizaciones/guardar")
def cotizacion_guardar(request: Request, cliente_id: int = Form(...), items_json: str = Form(...),
                       cotizacion_id: str = Form(""), fecha: str = Form(""),
                       validez_dias: int = Form(15), descuento: float = Form(0),
                       tiempo_entrega: str = Form(""), forma_pago: str = Form(""),
                       condiciones: str = Form(""), notas: str = Form("")):
    u, r = _guard(request)
    if r:
        return r
    items = _items_de_form(items_json)
    if not items:
        return _volver("/admin/cotizaciones", "Agregue al menos un ítem a la cotización.", "error")
    kw = dict(fecha=fecha or date.today().isoformat(), validez_dias=validez_dias,
              descuento=descuento, tiempo_entrega=tiempo_entrega, forma_pago=forma_pago,
              condiciones=condiciones, notas=notas)
    if cotizacion_id:
        D.actualizar_cotizacion(int(cotizacion_id), items, u["email"], cliente_id=cliente_id, **kw)
        cid = int(cotizacion_id)
    else:
        cid = D.crear_cotizacion(cliente_id, items, u["email"], **kw)
    excel_sync.exportar_control()
    return _volver(f"/admin/cotizaciones/{cid}", "Cotización guardada.")


@router.get("/cotizaciones/{cid}")
def cotizacion_ver(request: Request, cid: int, aviso: str = "", tipo: str = "ok"):
    from ..main import render
    u, r = _guard(request)
    if r:
        return r
    c = D.cotizacion_completa(cid)
    if not c:
        return _volver("/admin/cotizaciones", "Cotización no encontrada.", "error")
    return render(request, "docs/cotizacion.html", seccion="cotizaciones", c=c, panel=True,
                  aviso=aviso, aviso_tipo=tipo)


@router.post("/cotizaciones/estado")
def cotizacion_estado(request: Request, cotizacion_id: int = Form(...), estado: str = Form(...)):
    u, r = _guard(request)
    if r:
        return r
    D.cambiar_estado_cotizacion(cotizacion_id, estado, u["email"])
    excel_sync.exportar_control()
    return _volver(f"/admin/cotizaciones/{cotizacion_id}",
                   f"Cotización marcada como <strong>{estado}</strong>.")


@router.post("/cotizaciones/remisionar")
def cotizacion_remisionar(request: Request, cotizacion_id: int = Form(...)):
    u, r = _guard(request)
    if r:
        return r
    rid = D.desde_cotizacion(cotizacion_id, u["email"])
    excel_sync.exportar_control()
    return _volver(f"/admin/remisiones/{rid}", "Remisión generada desde la cotización.")


@router.post("/cotizaciones/facturar")
def cotizacion_facturar(request: Request, cotizacion_id: int = Form(...)):
    u, r = _guard(request)
    if r:
        return r
    fid = D.factura_desde("cotizacion", cotizacion_id, u["email"])
    excel_sync.exportar_control()
    return _volver(f"/admin/facturas/{fid}", "Factura generada desde la cotización.")


# =====================================================================
#  REMISIONES Y DESPACHOS
# =====================================================================
@router.get("/remisiones")
def remisiones(request: Request, estado: str = "", q: str = "", aviso: str = "", tipo: str = "ok"):
    from ..main import render
    u, r = _guard(request)
    if r:
        return r
    sql = """SELECT re.*, cl.razon_social, co.numero AS cot FROM remisiones re
             JOIN clientes cl ON cl.id=re.cliente_id
             LEFT JOIN cotizaciones co ON co.id=re.cotizacion_id WHERE 1=1"""
    params = []
    if estado:
        sql += " AND re.estado=?"
        params.append(estado)
    if q:
        sql += " AND (re.numero LIKE ? OR cl.razon_social LIKE ?)"
        params += [f"%{q}%"] * 2
    sql += " ORDER BY re.id DESC LIMIT 300"
    return render(request, "admin/remisiones.html", seccion="remisiones",
                  remisiones=db.q(sql, params), estado=estado, q=q,
                  aviso=aviso, aviso_tipo=tipo)


@router.get("/despachos")
def despachos(request: Request, aviso: str = "", tipo: str = "ok"):
    from ..main import render
    u, r = _guard(request)
    if r:
        return r
    sql = """SELECT re.*, cl.razon_social, cl.telefono FROM remisiones re
             JOIN clientes cl ON cl.id=re.cliente_id WHERE re.estado=? ORDER BY re.fecha, re.id"""
    filas = {e: db.q(sql, (e,)) for e in ("pendiente", "despachada", "entregada")}
    for grupo in filas.values():
        for rem in grupo:
            rem["items"] = db.q("SELECT * FROM remision_items WHERE remision_id=? ORDER BY orden",
                                (rem["id"],))
    return render(request, "admin/despachos.html", seccion="despachos", grupos=filas,
                  aviso=aviso, aviso_tipo=tipo)


@router.get("/remisiones/nueva")
def remision_nueva(request: Request, cliente_id: str = ""):
    from ..main import render
    u, r = _guard(request)
    if r:
        return r
    return render(request, "admin/remision_editar.html", seccion="remisiones",
                  cliente_id=cliente_id, **_datos_editor())


@router.post("/remisiones/guardar")
def remision_guardar(request: Request, cliente_id: int = Form(...), items_json: str = Form(...),
                     fecha: str = Form(""), direccion_entrega: str = Form(""),
                     ciudad_entrega: str = Form(""), transportador: str = Form(""),
                     placa: str = Form(""), conductor: str = Form(""),
                     orden_compra: str = Form(""), observaciones: str = Form("")):
    u, r = _guard(request)
    if r:
        return r
    items = _items_de_form(items_json)
    if not items:
        return _volver("/admin/remisiones", "Agregue al menos un ítem a la remisión.", "error")
    iva = float(db.empresa().get("iva_defecto") or 19)
    for it in items:
        if not it.get("iva_pct"):
            it["iva_pct"] = iva
    rid = D.crear_remision(cliente_id, items, u["email"], fecha=fecha or date.today().isoformat(),
                           direccion_entrega=direccion_entrega, ciudad_entrega=ciudad_entrega,
                           transportador=transportador, placa=placa, conductor=conductor,
                           orden_compra=orden_compra, observaciones=observaciones)
    excel_sync.exportar_control()
    return _volver(f"/admin/remisiones/{rid}", "Remisión creada.")


@router.get("/remisiones/{rid}")
def remision_ver(request: Request, rid: int, aviso: str = "", tipo: str = "ok"):
    from ..main import render
    u, r = _guard(request)
    if r:
        return r
    rem = D.remision_completa(rid)
    if not rem:
        return _volver("/admin/remisiones", "Remisión no encontrada.", "error")
    return render(request, "docs/remision.html", seccion="remisiones", r=rem, panel=True,
                  aviso=aviso, aviso_tipo=tipo)


@router.post("/remisiones/despachar")
def remision_despachar(request: Request, remision_id: int = Form(...),
                       transportador: str = Form(""), placa: str = Form(""),
                       conductor: str = Form("")):
    u, r = _guard(request)
    if r:
        return r
    D.despachar(remision_id, u["email"], transportador=transportador, placa=placa,
                conductor=conductor)
    excel_sync.exportar_control()
    return _volver("/admin/despachos", "Remisión marcada como despachada.")


@router.post("/remisiones/entregar")
def remision_entregar(request: Request, remision_id: int = Form(...),
                      recibido_por: str = Form(...), fecha_entrega: str = Form("")):
    u, r = _guard(request)
    if r:
        return r
    D.marcar_entregada(remision_id, recibido_por, fecha_entrega, u["email"])
    excel_sync.exportar_control()
    return _volver("/admin/despachos", "Entrega registrada.")


@router.post("/remisiones/facturar")
def remision_facturar(request: Request, remision_id: int = Form(...)):
    u, r = _guard(request)
    if r:
        return r
    fid = D.factura_desde("remision", remision_id, u["email"])
    excel_sync.exportar_control()
    return _volver(f"/admin/facturas/{fid}", "Factura generada desde la remisión.")


# =====================================================================
#  FACTURAS
# =====================================================================
@router.get("/facturas")
def facturas(request: Request, estado: str = "", q: str = "", aviso: str = "", tipo: str = "ok"):
    from ..main import render
    u, r = _guard(request)
    if r:
        return r
    sql = """SELECT fa.*, cl.razon_social, cl.documento FROM facturas fa
             JOIN clientes cl ON cl.id=fa.cliente_id WHERE 1=1"""
    params = []
    if estado == "vencidas":
        sql += (" AND fa.saldo>0 AND fa.fecha_vencimiento<date('now','localtime') "
                "AND fa.estado NOT IN ('anulada','borrador','pagada')")
    elif estado:
        sql += " AND fa.estado=?"
        params.append(estado)
    if q:
        sql += " AND (fa.numero LIKE ? OR cl.razon_social LIKE ? OR cl.documento LIKE ?)"
        params += [f"%{q}%"] * 3
    sql += " ORDER BY fa.id DESC LIMIT 300"
    from ..dian import habilitada
    return render(request, "admin/facturas.html", seccion="facturas", facturas=db.q(sql, params),
                  estado=estado, q=q, aviso=aviso, aviso_tipo=tipo, dian_lista=habilitada())


@router.get("/facturas/nueva")
def factura_nueva(request: Request, cliente_id: str = ""):
    from ..main import render
    u, r = _guard(request)
    if r:
        return r
    return render(request, "admin/factura_editar.html", seccion="facturas",
                  cliente_id=cliente_id, **_datos_editor())


@router.post("/facturas/guardar")
def factura_guardar(request: Request, cliente_id: int = Form(...), items_json: str = Form(...),
                    fecha_emision: str = Form(""), forma_pago: str = Form("credito"),
                    medio_pago: str = Form("transferencia"), plazo: int = Form(30),
                    descuento: float = Form(0), orden_compra: str = Form(""),
                    observaciones: str = Form("")):
    u, r = _guard(request)
    if r:
        return r
    items = _items_de_form(items_json)
    if not items:
        return _volver("/admin/facturas", "Agregue al menos un ítem a la factura.", "error")
    fid = D.crear_factura(cliente_id, items, u["email"],
                          fecha_emision=fecha_emision or date.today().isoformat(),
                          forma_pago=forma_pago, medio_pago=medio_pago, plazo=plazo,
                          descuento=descuento, orden_compra=orden_compra,
                          observaciones=observaciones)
    excel_sync.exportar_control()
    return _volver(f"/admin/facturas/{fid}", "Factura creada en borrador.")


@router.get("/facturas/{fid}")
def factura_ver(request: Request, fid: int, aviso: str = "", tipo: str = "ok"):
    from ..main import render
    u, r = _guard(request)
    if r:
        return r
    f = D.factura_completa(fid)
    if not f:
        return _volver("/admin/facturas", "Factura no encontrada.", "error")
    from ..dian import habilitada
    return render(request, "docs/factura.html", seccion="facturas", f=f, panel=True,
                  aviso=aviso, aviso_tipo=tipo, dian_lista=habilitada())


@router.post("/facturas/emitir")
def factura_emitir(request: Request, factura_id: int = Form(...)):
    u, r = _guard(request)
    if r:
        return r
    res = D.emitir_factura(factura_id, u["email"])
    excel_sync.exportar_control()
    tipo = "ok" if res.get("ok") else "alerta"
    aviso = ("Factura emitida y aceptada por la DIAN." if res.get("ok")
             else f"Factura emitida y numerada (CUFE calculado). {res.get('mensaje','')}")
    return _volver(f"/admin/facturas/{factura_id}", aviso, tipo)


@router.post("/facturas/pago")
def factura_pago(request: Request, factura_id: int = Form(...), valor: float = Form(...),
                 medio: str = Form("transferencia"), referencia: str = Form(""),
                 fecha: str = Form("")):
    u, r = _guard(request)
    if r:
        return r
    D.registrar_pago(factura_id, valor, medio, referencia, u["email"], fecha)
    excel_sync.exportar_control()
    return _volver(f"/admin/facturas/{factura_id}", "Pago registrado.")


@router.post("/facturas/anular")
def factura_anular(request: Request, factura_id: int = Form(...)):
    u, r = _guard(request)
    if r:
        return r
    D.anular("factura", factura_id, u["email"])
    excel_sync.exportar_control()
    return _volver(f"/admin/facturas/{factura_id}", "Factura anulada.", "alerta")


@router.get("/facturas/{fid}/xml")
def factura_xml(request: Request, fid: int):
    from fastapi.responses import Response
    u, r = _guard(request)
    if r:
        return r
    from .. import dian
    f = D.factura_completa(fid)
    emp = db.empresa()
    f["hora_emision"] = "00:00:00-05:00"
    f["cliente_documento"] = f["cliente"]["documento"]
    xml = dian.generar_xml_ubl(f, emp, f["cliente"], f["items"])
    return Response(xml, media_type="application/xml", headers={
        "Content-Disposition": f'attachment; filename="{f["numero"]}.xml"'})


# =====================================================================
#  CATÁLOGO WEB
# =====================================================================
@router.get("/catalogo")
def catalogo(request: Request, q: str = "", aviso: str = "", tipo: str = "ok"):
    from ..main import render
    u, r = _guard(request)
    if r:
        return r
    sql = """SELECT p.*, c.nombre AS categoria FROM productos p
             JOIN categorias c ON c.id=p.categoria_id WHERE 1=1"""
    params = []
    if q:
        sql += " AND (p.nombre LIKE ? OR p.sku LIKE ?)"
        params += [f"%{q}%"] * 2
    sql += " ORDER BY c.orden, p.nombre"
    return render(request, "admin/catalogo.html", seccion="catalogo", productos=db.q(sql, params),
                  categorias=db.q("SELECT * FROM categorias ORDER BY orden"), q=q,
                  aviso=aviso, aviso_tipo=tipo)


@router.post("/catalogo/guardar")
def catalogo_guardar(request: Request, nombre: str = Form(...), sku: str = Form(...),
                     categoria_id: int = Form(...), descripcion: str = Form(""),
                     especificaciones: str = Form(""), material: str = Form(""),
                     unidad: str = Form("UND"), precio: float = Form(0),
                     iva_pct: float = Form(19), dias_entrega: int = Form(15),
                     destacado: str = Form(""), activo: str = Form("1"),
                     producto_id: str = Form(""), imagen: UploadFile | None = File(None)):
    u, r = _guard(request)
    if r:
        return r
    ruta_img = None
    if imagen and imagen.filename:
        ext = "." + imagen.filename.rsplit(".", 1)[-1].lower()
        if ext in (".jpg", ".jpeg", ".png", ".webp"):
            nombre_arch = f"{slugify(sku)}-{datetime.now():%Y%m%d%H%M%S}{ext}"
            with (IMAGENES_DIR / nombre_arch).open("wb") as f:
                shutil.copyfileobj(imagen.file, f)
            ruta_img = f"/subidas/{nombre_arch}"

    campos = (sku.strip(), nombre.strip(), categoria_id, descripcion, especificaciones, material,
              unidad, precio, iva_pct, dias_entrega, 1 if destacado else 0, 1 if activo else 0)
    if producto_id:
        db.ex("""UPDATE productos SET sku=?,nombre=?,categoria_id=?,descripcion=?,
                 especificaciones=?,material=?,unidad=?,precio=?,iva_pct=?,dias_entrega=?,
                 destacado=?,activo=? WHERE id=?""", (*campos, producto_id))
        if ruta_img:
            db.ex("UPDATE productos SET imagen=? WHERE id=?", (ruta_img, producto_id))
        aviso = f"Producto <strong>{nombre}</strong> actualizado."
    else:
        if db.q1("SELECT 1 FROM productos WHERE sku=?", (sku.strip(),)):
            return _volver("/admin/catalogo", f"Ya existe un producto con el SKU {sku}.", "error")
        db.ex("""INSERT INTO productos(sku,nombre,categoria_id,descripcion,especificaciones,
                 material,unidad,precio,iva_pct,dias_entrega,destacado,activo,slug,imagen)
                 VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
              (*campos, slugify(nombre), ruta_img or ""))
        aviso = f"Producto <strong>{nombre}</strong> publicado en el catálogo."
    db.log(u["email"], "guardar", "producto", sku)
    excel_sync.exportar_control()
    return _volver("/admin/catalogo", aviso)


# =====================================================================
#  EXCEL, USUARIOS, CONFIGURACIÓN, BITÁCORA
# =====================================================================
@router.get("/excel")
def excel(request: Request, aviso: str = "", tipo: str = "ok"):
    from ..main import render
    u, r = _guard(request)
    if r:
        return r
    def info(ruta):
        if not ruta.exists():
            return None
        st = ruta.stat()
        return {"nombre": ruta.name, "kb": round(st.st_size / 1024),
                "fecha": datetime.fromtimestamp(st.st_mtime).strftime("%d/%m/%Y %I:%M %p")}
    return render(request, "admin/excel.html", seccion="excel", aviso=aviso, aviso_tipo=tipo,
                  control=info(excel_sync.RUTA_CONTROL), respaldo=info(excel_sync.RUTA_RESPALDO),
                  bd_kb=round(DB_PATH.stat().st_size / 1024) if DB_PATH.exists() else 0)


@router.post("/excel/generar")
def excel_generar(request: Request):
    u, r = _guard(request)
    if r:
        return r
    excel_sync.exportar_todo()
    db.log(u["email"], "exportar", "excel")
    return _volver("/admin/excel", "Los dos archivos de Excel fueron regenerados.")


@router.get("/excel/descargar/{cual}")
def excel_descargar(request: Request, cual: str):
    u, r = _guard(request)
    if r:
        return r
    ruta = excel_sync.RUTA_CONTROL if cual == "control" else excel_sync.RUTA_RESPALDO
    if not ruta.exists():
        excel_sync.exportar_todo()
    return FileResponse(ruta, filename=ruta.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.get("/excel/base-datos")
def descargar_bd(request: Request):
    u, r = _guard(request)
    if r:
        return r
    copia = UPLOAD_DIR / f"imatec_{datetime.now():%Y%m%d_%H%M%S}.db"
    shutil.copy2(DB_PATH, copia)
    return FileResponse(copia, filename=copia.name, media_type="application/octet-stream")


@router.get("/usuarios")
def usuarios(request: Request, aviso: str = "", tipo: str = "ok"):
    from ..main import render
    u, r = _guard(request)
    if r:
        return r
    return render(request, "admin/usuarios.html", seccion="usuarios", aviso=aviso, aviso_tipo=tipo,
        usuarios=db.q("""SELECT us.*, cl.razon_social FROM usuarios us
                         LEFT JOIN clientes cl ON cl.id=us.cliente_id ORDER BY us.rol, us.nombre"""),
        clientes=db.q("SELECT id,razon_social FROM clientes WHERE activo=1 ORDER BY razon_social"))


@router.post("/usuarios/guardar")
def usuarios_guardar(request: Request, nombre: str = Form(...), email: str = Form(...),
                     rol: str = Form("cliente"), password: str = Form(""),
                     cliente_id: str = Form(""), usuario_id: str = Form(""),
                     activo: str = Form("1")):
    u, r = _guard(request)
    if r:
        return r
    cid = int(cliente_id) if cliente_id and rol == "cliente" else None
    if usuario_id:
        db.ex("UPDATE usuarios SET nombre=?,email=?,rol=?,cliente_id=?,activo=? WHERE id=?",
              (nombre, email.strip().lower(), rol, cid, 1 if activo else 0, usuario_id))
        if password.strip():
            db.ex("UPDATE usuarios SET password_hash=? WHERE id=?",
                  (hash_password(password.strip()), usuario_id))
        aviso = f"Usuario <strong>{nombre}</strong> actualizado."
    else:
        if db.q1("SELECT 1 FROM usuarios WHERE lower(email)=lower(?)", (email,)):
            return _volver("/admin/usuarios", "Ya existe un usuario con ese correo.", "error")
        clave = password.strip() or "Imatec2026*"
        crear_usuario(email, clave, nombre, rol, cid)
        aviso = f"Usuario creado. Contraseña: <strong>{clave}</strong>"
    db.log(u["email"], "guardar", "usuario", email)
    return _volver("/admin/usuarios", aviso)


@router.get("/configuracion")
def configuracion(request: Request, aviso: str = "", tipo: str = "ok"):
    from ..main import render
    u, r = _guard(request)
    if r:
        return r
    from ..dian import habilitada
    return render(request, "admin/configuracion.html", seccion="configuracion",
                  aviso=aviso, aviso_tipo=tipo, e=db.empresa(), dian_lista=habilitada(),
                  listas={l: db.opciones(l) for l in ("categoria", "material", "diametro", "unidad")})


@router.post("/configuracion/guardar")
async def configuracion_guardar(request: Request):
    u, r = _guard(request)
    if r:
        return r
    form = await request.form()
    for clave, valor in form.items():
        if clave.startswith("empresa."):
            db.set_config(clave, str(valor))
    db.log(u["email"], "configurar", "empresa")
    return _volver("/admin/configuracion", "Configuración guardada.")


@router.post("/configuracion/lista")
def configuracion_lista(request: Request, lista: str = Form(...), valor: str = Form(""),
                        eliminar: str = Form("")):
    u, r = _guard(request)
    if r:
        return r
    if eliminar:
        db.ex("DELETE FROM listas WHERE lista=? AND valor=?", (lista, eliminar))
        aviso = f"Se quitó «{eliminar}» de la lista de {lista}."
    elif valor.strip():
        db.ex("INSERT OR IGNORE INTO listas(lista,valor,orden) VALUES(?,?,99)",
              (lista, valor.strip()))
        aviso = f"Se agregó «{valor.strip()}» a la lista de {lista}."
    else:
        aviso = "No se indicó ningún valor."
    excel_sync.exportar_control()
    return _volver("/admin/configuracion", aviso)


@router.get("/bitacora")
def bitacora(request: Request):
    from ..main import render
    u, r = _guard(request)
    if r:
        return r
    return render(request, "admin/bitacora.html", seccion="bitacora",
                  registros=db.q("SELECT * FROM bitacora ORDER BY id DESC LIMIT 400"),
                  mensajes=db.q("SELECT * FROM mensajes ORDER BY id DESC LIMIT 60"))
