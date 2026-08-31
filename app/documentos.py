"""Lógica de negocio: pedidos -> cotización -> remisión -> factura."""
from datetime import date

from . import db
from .numbering import numero as nuevo_numero
from .utils import calcular_totales, sumar_dias


# ------------------------------------------------------------------ lectura
def _iva_defecto() -> float:
    return float(db.empresa().get("iva_defecto") or 19)


def _items(tabla: str, campo: str, doc_id: int) -> list:
    return db.q(f"SELECT * FROM {tabla} WHERE {campo}=? ORDER BY orden, id", (doc_id,))


def cotizacion_completa(cid: int) -> dict | None:
    c = db.q1("SELECT * FROM cotizaciones WHERE id=?", (cid,))
    if not c:
        return None
    c["cliente"] = db.q1("SELECT * FROM clientes WHERE id=?", (c["cliente_id"],))
    c["items"] = _items("cotizacion_items", "cotizacion_id", cid)
    c["vence"] = sumar_dias(c["fecha"], c["validez_dias"])
    c["remisiones"] = db.q("SELECT id,numero,fecha,estado FROM remisiones WHERE cotizacion_id=?", (cid,))
    c["facturas"] = db.q("SELECT id,numero,fecha_emision,estado FROM facturas WHERE cotizacion_id=?", (cid,))
    return c


def remision_completa(rid: int) -> dict | None:
    r = db.q1("SELECT * FROM remisiones WHERE id=?", (rid,))
    if not r:
        return None
    r["cliente"] = db.q1("SELECT * FROM clientes WHERE id=?", (r["cliente_id"],))
    r["items"] = _items("remision_items", "remision_id", rid)
    r["cotizacion"] = db.q1("SELECT id,numero FROM cotizaciones WHERE id=?", (r["cotizacion_id"],)) \
        if r["cotizacion_id"] else None
    r["facturas"] = db.q("SELECT id,numero,estado FROM facturas WHERE remision_id=?", (rid,))
    return r


def factura_completa(fid: int) -> dict | None:
    f = db.q1("SELECT * FROM facturas WHERE id=?", (fid,))
    if not f:
        return None
    f["cliente"] = db.q1("SELECT * FROM clientes WHERE id=?", (f["cliente_id"],))
    f["items"] = _items("factura_items", "factura_id", fid)
    f["pagos"] = db.q("SELECT * FROM pagos WHERE factura_id=? ORDER BY fecha, id", (fid,))
    f["remision"] = db.q1("SELECT id,numero FROM remisiones WHERE id=?", (f["remision_id"],)) \
        if f["remision_id"] else None
    f["cotizacion"] = db.q1("SELECT id,numero FROM cotizaciones WHERE id=?", (f["cotizacion_id"],)) \
        if f["cotizacion_id"] else None
    return f


def pedido_completo(pid: int) -> dict | None:
    p = db.q1("SELECT * FROM pedidos WHERE id=?", (pid,))
    if not p:
        return None
    p["cliente"] = db.q1("SELECT * FROM clientes WHERE id=?", (p["cliente_id"],)) \
        if p["cliente_id"] else None
    p["items"] = db.q("SELECT * FROM pedido_items WHERE pedido_id=? ORDER BY id", (pid,))
    p["cotizaciones"] = db.q("SELECT id,numero,estado FROM cotizaciones WHERE pedido_id=?", (pid,))
    return p


# ------------------------------------------------------------------ cotización
def crear_cotizacion(cliente_id: int, items: list, usuario: str = "", **kw) -> int:
    tot = calcular_totales(items, kw.get("descuento", 0))
    num = nuevo_numero("cotizacion")
    emp = db.empresa()
    cid = db.ex("""INSERT INTO cotizaciones
        (numero,cliente_id,pedido_id,fecha,validez_dias,estado,subtotal,descuento,iva,total,
         tiempo_entrega,forma_pago,condiciones,notas,elaborado_por)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (num, cliente_id, kw.get("pedido_id"), kw.get("fecha") or date.today().isoformat(),
         int(kw.get("validez_dias") or emp.get("validez_cotizacion_dias") or 15),
         kw.get("estado", "borrador"), tot["subtotal"], tot["descuento"], tot["iva"], tot["total"],
         kw.get("tiempo_entrega", "15 días hábiles"),
         kw.get("forma_pago", "50% anticipo, 50% contra entrega"),
         kw.get("condiciones", ""), kw.get("notas", ""), usuario))
    _guardar_items("cotizacion_items", "cotizacion_id", cid, items, con_impuestos=True)
    if kw.get("pedido_id"):
        db.ex("UPDATE pedidos SET estado='cotizado' WHERE id=?", (kw["pedido_id"],))
    db.log(usuario, "crear", "cotizacion", num, f"Cliente {cliente_id} — total {tot['total']}")
    return cid


def actualizar_cotizacion(cid: int, items: list, usuario: str = "", **kw) -> None:
    tot = calcular_totales(items, kw.get("descuento", 0))
    db.ex("""UPDATE cotizaciones SET cliente_id=COALESCE(?,cliente_id), fecha=COALESCE(?,fecha),
             validez_dias=COALESCE(?,validez_dias), subtotal=?, descuento=?, iva=?, total=?,
             tiempo_entrega=COALESCE(?,tiempo_entrega), forma_pago=COALESCE(?,forma_pago),
             condiciones=COALESCE(?,condiciones), notas=COALESCE(?,notas)
             WHERE id=?""",
          (kw.get("cliente_id"), kw.get("fecha"), kw.get("validez_dias"),
           tot["subtotal"], tot["descuento"], tot["iva"], tot["total"],
           kw.get("tiempo_entrega"), kw.get("forma_pago"), kw.get("condiciones"),
           kw.get("notas"), cid))
    db.ex("DELETE FROM cotizacion_items WHERE cotizacion_id=?", (cid,))
    _guardar_items("cotizacion_items", "cotizacion_id", cid, items, con_impuestos=True)
    db.log(usuario, "actualizar", "cotizacion", str(cid), f"total {tot['total']}")


def _guardar_items(tabla, campo, doc_id, items, con_impuestos=False) -> None:
    for orden, it in enumerate(items, start=1):
        if con_impuestos:
            db.ex(f"""INSERT INTO {tabla}
                ({campo},producto_id,orden,descripcion,especificaciones,cantidad,unidad,
                 precio,descuento_pct,iva_pct,total)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (doc_id, it.get("producto_id") or None, orden, it["descripcion"],
                 it.get("especificaciones", ""), float(it.get("cantidad") or 0),
                 it.get("unidad", "UND"), float(it.get("precio") or 0),
                 float(it.get("descuento_pct") or 0), float(it.get("iva_pct") or 0),
                 float(it.get("total") or 0)))
        else:
            db.ex(f"""INSERT INTO {tabla}
                ({campo},producto_id,orden,descripcion,cantidad,unidad,precio,
                 descuento_pct,iva_pct,observacion)
                VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (doc_id, it.get("producto_id") or None, orden, it["descripcion"],
                 float(it.get("cantidad") or 0), it.get("unidad", "UND"),
                 float(it.get("precio") or 0), float(it.get("descuento_pct") or 0),
                 float(it.get("iva_pct") or _iva_defecto()), it.get("observacion", "")))


def cambiar_estado_cotizacion(cid: int, estado: str, usuario: str = "") -> None:
    db.ex("UPDATE cotizaciones SET estado=? WHERE id=?", (estado, cid))
    db.log(usuario, "estado", "cotizacion", str(cid), estado)


# ------------------------------------------------------------------ remisión
def crear_remision(cliente_id: int, items: list, usuario: str = "", **kw) -> int:
    num = nuevo_numero("remision")
    cli = db.q1("SELECT * FROM clientes WHERE id=?", (cliente_id,)) or {}
    rid = db.ex("""INSERT INTO remisiones
        (numero,cliente_id,cotizacion_id,fecha,estado,direccion_entrega,ciudad_entrega,
         transportador,placa,conductor,orden_compra,observaciones,elaborado_por)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (num, cliente_id, kw.get("cotizacion_id"), kw.get("fecha") or date.today().isoformat(),
         kw.get("estado", "pendiente"),
         kw.get("direccion_entrega") or cli.get("direccion", ""),
         kw.get("ciudad_entrega") or cli.get("ciudad", ""),
         kw.get("transportador", ""), kw.get("placa", ""), kw.get("conductor", ""),
         kw.get("orden_compra", ""), kw.get("observaciones", ""), usuario))
    _guardar_items("remision_items", "remision_id", rid, items)
    db.log(usuario, "crear", "remision", num, f"Cliente {cliente_id}")
    return rid


def desde_cotizacion(cid: int, usuario: str = "", **kw) -> int:
    """Genera la remisión copiando los ítems de la cotización aprobada."""
    c = cotizacion_completa(cid)
    items = [{"producto_id": i["producto_id"], "descripcion": i["descripcion"],
              "cantidad": i["cantidad"], "unidad": i["unidad"], "precio": i["precio"],
              "descuento_pct": i["descuento_pct"], "iva_pct": i["iva_pct"],
              "observacion": ""} for i in c["items"]]
    return crear_remision(c["cliente_id"], items, usuario, cotizacion_id=cid, **kw)


def despachar(rid: int, usuario: str = "", **kw) -> None:
    db.ex("""UPDATE remisiones SET estado='despachada', transportador=COALESCE(?,transportador),
             placa=COALESCE(?,placa), conductor=COALESCE(?,conductor) WHERE id=?""",
          (kw.get("transportador"), kw.get("placa"), kw.get("conductor"), rid))
    db.log(usuario, "despachar", "remision", str(rid), kw.get("transportador", ""))


def marcar_entregada(rid: int, recibido_por: str, fecha_entrega: str = "", usuario: str = "") -> None:
    db.ex("UPDATE remisiones SET estado='entregada', recibido_por=?, fecha_entrega=? WHERE id=?",
          (recibido_por, fecha_entrega or date.today().isoformat(), rid))
    db.log(usuario, "entregar", "remision", str(rid), recibido_por)


# ------------------------------------------------------------------ factura
def crear_factura(cliente_id: int, items: list, usuario: str = "", **kw) -> int:
    tot = calcular_totales(items, kw.get("descuento", 0))
    num, consecutivo = nuevo_numero("factura")
    emp = db.empresa()
    cli = db.q1("SELECT * FROM clientes WHERE id=?", (cliente_id,)) or {}
    fecha = kw.get("fecha_emision") or date.today().isoformat()
    plazo = int(kw.get("plazo") or cli.get("condicion_pago") or emp.get("plazo_factura_dias") or 30)
    forma = kw.get("forma_pago", "credito")
    fid = db.ex("""INSERT INTO facturas
        (numero,prefijo,consecutivo,cliente_id,cotizacion_id,remision_id,fecha_emision,
         fecha_vencimiento,forma_pago,medio_pago,subtotal,descuento,iva,total,saldo,estado,
         orden_compra,observaciones,elaborado_por,resolucion_dian)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (num, emp.get("dian_prefijo", "FE"), consecutivo, cliente_id, kw.get("cotizacion_id"),
         kw.get("remision_id"), fecha,
         fecha if forma == "contado" else sumar_dias(fecha, plazo),
         forma, kw.get("medio_pago", "transferencia"),
         tot["subtotal"], tot["descuento"], tot["iva"], tot["total"], tot["total"],
         kw.get("estado", "borrador"), kw.get("orden_compra", ""),
         kw.get("observaciones", ""), usuario, emp.get("dian_resolucion", "")))
    _guardar_items("factura_items", "factura_id", fid, items, con_impuestos=True)
    db.log(usuario, "crear", "factura", num, f"Cliente {cliente_id} — total {tot['total']}")
    return fid


def factura_desde(origen: str, oid: int, usuario: str = "", **kw) -> int:
    """origen: 'cotizacion' o 'remision'."""
    if origen == "cotizacion":
        d = cotizacion_completa(oid)
        items = [dict(i) for i in d["items"]]
        kw.setdefault("cotizacion_id", oid)
        kw.setdefault("orden_compra", "")
    else:
        d = remision_completa(oid)
        items = [{"producto_id": i["producto_id"], "descripcion": i["descripcion"],
                  "cantidad": i["cantidad"], "unidad": i["unidad"], "precio": i["precio"],
                  "descuento_pct": i["descuento_pct"], "iva_pct": i["iva_pct"]}
                 for i in d["items"]]
        # El descuento global pactado en la cotización también se conserva
        if d["cotizacion_id"]:
            cot = db.q1("SELECT descuento FROM cotizaciones WHERE id=?", (d["cotizacion_id"],))
            if cot:
                kw.setdefault("descuento", cot["descuento"])
        kw.setdefault("remision_id", oid)
        kw.setdefault("cotizacion_id", d["cotizacion_id"])
        kw.setdefault("orden_compra", d.get("orden_compra", ""))
    return crear_factura(d["cliente_id"], items, usuario, **kw)


def emitir_factura(fid: int, usuario: str = "") -> dict:
    """Deja la factura en firme, calcula CUFE/QR e intenta transmitirla a la DIAN."""
    from . import dian
    datos = dian.preparar(fid)
    envio = dian.enviar_a_dian(fid)
    estado = "aceptada" if envio.get("ok") else "emitida"
    db.ex("UPDATE facturas SET estado=? WHERE id=? AND estado='borrador'", (estado, fid))
    db.log(usuario, "emitir", "factura", str(fid), envio.get("mensaje", ""))
    return {**datos, **envio, "estado": estado}


def registrar_pago(fid: int, valor: float, medio: str = "transferencia",
                   referencia: str = "", usuario: str = "", fecha: str = "") -> None:
    db.ex("""INSERT INTO pagos(factura_id,fecha,valor,medio,referencia,registrado_por)
             VALUES(?,?,?,?,?,?)""",
          (fid, fecha or date.today().isoformat(), float(valor), medio, referencia, usuario))
    pagado = db.scalar("SELECT COALESCE(SUM(valor),0) FROM pagos WHERE factura_id=?", (fid,))
    f = db.q1("SELECT total,estado FROM facturas WHERE id=?", (fid,))
    saldo = round(float(f["total"]) - float(pagado), 2)
    nuevo_estado = "pagada" if saldo <= 0.01 else f["estado"]
    db.ex("UPDATE facturas SET saldo=?, estado=? WHERE id=?", (max(saldo, 0), nuevo_estado, fid))
    db.log(usuario, "pago", "factura", str(fid), f"{valor} — saldo {saldo}")


def anular(tipo: str, doc_id: int, usuario: str = "") -> None:
    tabla = {"cotizacion": "cotizaciones", "remision": "remisiones", "factura": "facturas"}[tipo]
    db.ex(f"UPDATE {tabla} SET estado='anulada' WHERE id=?", (doc_id,))
    db.log(usuario, "anular", tipo, str(doc_id))


# ------------------------------------------------------------------ pedidos web
def crear_pedido(items: list, usuario: str = "", **kw) -> int:
    num = nuevo_numero("pedido")
    total = sum(float(i.get("cantidad") or 0) * float(i.get("precio") or 0) for i in items)
    pid = db.ex("""INSERT INTO pedidos
        (numero,cliente_id,nombre_contacto,email,telefono,empresa,estado,notas,total_estimado)
        VALUES(?,?,?,?,?,?,?,?,?)""",
        (num, kw.get("cliente_id"), kw.get("nombre_contacto", ""), kw.get("email", ""),
         kw.get("telefono", ""), kw.get("empresa", ""), "nuevo", kw.get("notas", ""), total))
    for it in items:
        db.ex("""INSERT INTO pedido_items
                 (pedido_id,producto_id,material_id,descripcion,cantidad,unidad,precio,observacion)
                 VALUES(?,?,?,?,?,?,?,?)""",
              (pid, it.get("producto_id") or None, it.get("material_id") or None,
               it["descripcion"], float(it.get("cantidad") or 1), it.get("unidad", "UND"),
               float(it.get("precio") or 0), it.get("observacion", "")))
    db.log(usuario or kw.get("email", ""), "crear", "pedido", num, kw.get("empresa", ""))
    return pid


def pedido_a_cotizacion(pid: int, cliente_id: int, usuario: str = "") -> int:
    p = pedido_completo(pid)
    iva = float(db.empresa().get("iva_defecto") or 19)
    items = [{"producto_id": i["producto_id"], "descripcion": i["descripcion"],
              "especificaciones": i["observacion"], "cantidad": i["cantidad"],
              "unidad": i["unidad"], "precio": i["precio"], "descuento_pct": 0,
              "iva_pct": iva} for i in p["items"]]
    db.ex("UPDATE pedidos SET estado='en_cotizacion' WHERE id=?", (pid,))
    return crear_cotizacion(cliente_id, items, usuario, pedido_id=pid,
                            notas=p["notas"] or "")
