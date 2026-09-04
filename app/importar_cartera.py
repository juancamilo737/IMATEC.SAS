"""Carga la cartera real desde «RELACION DE CARTERA IMATEC S.A.S.xlsx».

El archivo trae: cliente, número de factura, valor y fecha de vencimiento
repartida en tres columnas (día, mes, año). Cada fila se convierte en una
factura ya emitida con su saldo pendiente, para que el estado de cuenta del
portal refleje la deuda real y no arranque en cero.

Los nombres del archivo vienen abreviados («TUVACOL», «V A A SOLUCIONES»),
así que se cruzan contra los clientes por coincidencia de nombre normalizado.
Lo que no cruza se reporta en vez de inventarse un cliente.

DOS ERRORES QUE HICIERON QUE LA CARTERA SALIERA INFLADA
-------------------------------------------------------
El dueño revisó la primera carga y dijo que no se debía todo eso. Tenía
razón, y el propio archivo lo demuestra:

1. **Se leían las dos hojas.** La «Hoja1» es la relación de cartera y trae su
   propio total escrito al pie: 29.743.442. La «Hoja2» es otra cosa —un
   ESTADO DE CUENTA de un solo cliente, FERRETERIA SU PROVEEDOR, con 15
   facturas más viejas (FEV-453 a FEV-560)— y **no está sumada dentro de ese
   total**. Ese mismo cliente sí aparece en la Hoja1, con sus 4 facturas
   nuevas (FEV-628 en adelante). Cargar las dos hojas sumaba 16.420.071 que
   la empresa no considera cartera vigente. Ahora sólo se lee la hoja que se
   llama relación de cartera; cualquier otra se reporta como omitida.

2. **Se botaban las filas sin fecha de vencimiento.** Nueve facturas dicen
   «PDTE PAGO» en la columna del día, y el importador las descartaba: eran
   7.151.775 que sí se deben. La prueba de que cuentan es aritmética: las 47
   filas de la Hoja1, incluidas esas nueve, suman exactamente el total que
   ellos escribieron al pie. Ahora entran con la fecha de vencimiento vacía y
   quedan en su propia franja de cobranza, sin inventarles un plazo.

El resultado se compara contra el total escrito en la hoja y se reporta la
diferencia. Si no cuadra, es que el archivo cambió y hay que mirarlo.
"""
import difflib
import unicodedata
from datetime import date
from pathlib import Path

from openpyxl import load_workbook

from . import db

# Marca las facturas que creó este importador. Sólo esas se tocan al recargar:
# una factura hecha desde el panel nunca se pisa ni se borra.
MARCA = "Saldo trasladado de la relación de cartera"


def _norm(t) -> str:
    t = unicodedata.normalize("NFKD", str(t or "")).encode("ascii", "ignore").decode()
    t = "".join(c for c in t.upper() if c.isalnum() or c == " ")
    for palabra in (" SAS", " S A S", " SA", " ESP", " E S P", " LTDA", " CIA", " Y CIA"):
        t = t.replace(palabra, " ")
    return " ".join(t.split())


def _buscar_cliente(nombre: str, indice: dict):
    """La relación de cartera se escribió a mano, así que trae erratas
    («FERRETRIA» por «FERRETERIA»), letras invertidas («C V» por «VC») y
    nombres abreviados. Se busca en tres pasadas, de más estricta a más laxa."""
    n = _norm(nombre)
    if not n:
        return None
    if n in indice:
        return indice[n]
    for clave, cid in indice.items():          # uno contenido en el otro
        if len(n) >= 6 and (n in clave or clave in n):
            return cid
    # parecido tipográfico, para las erratas
    cercanos = difflib.get_close_matches(n, list(indice), n=1, cutoff=0.82)
    if cercanos:
        return indice[cercanos[0]]
    # mismas palabras en distinto orden («EMERGENCIAS INDUSTRIALES C V» / «... VC»)
    pal = set(n.split())
    if len(pal) >= 2:
        for clave, cid in indice.items():
            otras = set(clave.split())
            comunes = pal & otras
            if len(comunes) >= 2 and len(comunes) >= min(len(pal), len(otras)) - 1:
                return cid
    return None


def _crear_cliente_minimo(nombre: str) -> int:
    """Un cliente que debe plata pero no está en el maestro de Xubio.
    Se crea con lo poco que hay: perder la deuda sería peor que tener una
    ficha incompleta. Queda marcado para que alguien la complete."""
    n = db.scalar("SELECT COUNT(*) FROM clientes") + 1
    return db.ex("""INSERT INTO clientes(codigo,tipo_documento,documento,razon_social,
                    ciudad,departamento,notas)
                    VALUES(?,'NIT','',?,'','','Creado desde la relación de cartera — faltan NIT y datos de contacto')""",
                 (f"CL-{n:04d}", " ".join(str(nombre).split())))


def _es_hoja_de_cartera(ws) -> bool:
    """Distingue la relación de cartera de un estado de cuenta suelto.

    Se mira el título de la hoja, no su posición: si mañana agregan una hoja
    antes, la posición mentiría y el título no.
    """
    for fila in ws.iter_rows(min_row=1, max_row=3, values_only=True):
        for celda in fila:
            if celda and "RELACION" in _norm(celda) and "CARTERA" in _norm(celda):
                return True
    return False


def _total_escrito(ws) -> float:
    """El total que la empresa escribió al pie de la hoja: la fila que trae
    un valor en la columna de importes pero ninguna factura ni cliente. Es la
    cifra contra la que hay que cuadrar."""
    total = 0.0
    for fila in ws.iter_rows(min_row=2, values_only=True):
        vals = list(fila) + [None] * 10
        if vals[0] or vals[4]:
            continue
        if isinstance(vals[5], (int, float)) and vals[5] > 0:
            total = float(vals[5])
    return total


def _leer_hoja(ws) -> list:
    """Filas aprovechables de la hoja, con la fecha ya resuelta.

    `vence` queda vacío cuando el archivo dice «PDTE PAGO» en vez de una
    fecha: son facturas que sí se deben pero a las que nadie les puso plazo.
    Se guarda como cadena vacía —el valor por defecto de la columna— y no como
    una fecha inventada: la antigüedad de esa deuda no se puede calcular, y
    fingir que sí la coloca en una franja de cobranza que no le corresponde.
    """
    filas = []
    for fila in ws.iter_rows(min_row=2, values_only=True):
        vals = list(fila) + [None] * 10
        nombre, numero, valor = vals[0], vals[4], vals[5]
        dd, mm, aa = vals[6], vals[7], vals[8]
        if not nombre or not isinstance(valor, (int, float)) or valor <= 0:
            continue

        numero = str(numero or "").strip() or f"SIN-NUM-{int(valor)}"
        if not numero.upper().startswith("FEV"):
            numero = f"FEV-{numero}"

        vence = ""
        if all(isinstance(x, (int, float)) for x in (dd, mm, aa)):
            try:
                vence = date(int(aa), int(mm), int(dd)).isoformat()
            except ValueError:
                vence = ""

        # La columna «CDO» lleva anotaciones a mano —«ABONÓ» en una— que no
        # se pueden convertir en un pago porque no dicen de cuánto. Se
        # arrastran al documento para que quien cobre las vea.
        nota = ""
        for extra in vals[9:12]:
            if isinstance(extra, str) and extra.strip():
                nota = extra.strip()
                break

        filas.append({"cliente": str(nombre).strip(), "numero": numero,
                      "total": round(float(valor), 2), "vence": vence, "nota": nota})
    return filas


def importar_cartera(ruta, usuario: str = "relación de cartera") -> dict:
    wb = load_workbook(Path(ruta), data_only=True)
    indice = {_norm(c["razon_social"]): c["id"]
              for c in db.q("SELECT id, razon_social FROM clientes")}
    for c in db.q("SELECT id, nombre_comercial FROM clientes WHERE nombre_comercial<>''"):
        indice.setdefault(_norm(c["nombre_comercial"]), c["id"])

    res = {"creadas": 0, "actualizadas": 0, "retiradas": 0, "sin_fecha": 0,
           "sin_cliente": [], "hojas_omitidas": [], "respetadas": [],
           "total": 0.0, "total_escrito": 0.0}

    filas, vistas = [], set()
    for ws in wb.worksheets:
        if not _es_hoja_de_cartera(ws):
            res["hojas_omitidas"].append(ws.title)
            continue
        res["total_escrito"] += _total_escrito(ws)
        for f in _leer_hoja(ws):
            if f["numero"] in vistas:            # la misma factura en dos hojas
                continue
            vistas.add(f["numero"])
            filas.append(f)

    previas = {f["numero"]: f for f in db.q(
        "SELECT id, numero, total, saldo FROM facturas WHERE observaciones LIKE ?",
        (MARCA + "%",))}

    for f in filas:
        cid = _buscar_cliente(f["cliente"], indice)
        if not cid:
            cid = _crear_cliente_minimo(f["cliente"])
            indice[_norm(f["cliente"])] = cid
            res["sin_cliente"].append(f["cliente"])

        obs = MARCA
        if not f["vence"]:
            obs += " — el archivo dice «PDTE PAGO»: falta acordar la fecha de vencimiento"
            res["sin_fecha"] += 1
        if f["nota"]:
            obs += f" — anotado en el archivo: «{f['nota']}»"

        total = f["total"]
        base = round(total / 1.19, 2)
        previa = previas.pop(f["numero"], None)

        if previa is None:
            db.ex("""INSERT INTO facturas
                     (numero,prefijo,consecutivo,cliente_id,fecha_emision,fecha_vencimiento,
                      forma_pago,medio_pago,subtotal,descuento,iva,total,saldo,estado,
                      observaciones,elaborado_por)
                     VALUES(?,?,0,?,?,?,'credito','transferencia',?,0,?,?,?,'emitida',?,?)""",
                  (f["numero"], "FEV", cid, f["vence"], f["vence"], base,
                   round(total - base, 2), total, total, obs, usuario))
            res["creadas"] += 1
        elif abs(float(previa["saldo"] or 0) - float(previa["total"] or 0)) > 0.01:
            # Alguien ya registró un abono contra esta factura: el archivo no
            # sabe de eso, así que manda lo registrado en el sistema.
            res["respetadas"].append(f["numero"])
        else:
            db.ex("""UPDATE facturas SET cliente_id=?, fecha_emision=?, fecha_vencimiento=?,
                     subtotal=?, iva=?, total=?, saldo=?, observaciones=? WHERE id=?""",
                  (cid, f["vence"], f["vence"], base, round(total - base, 2),
                   total, total, obs, previa["id"]))
            res["actualizadas"] += 1
        res["total"] += total

    # Lo que este importador había creado y ya no está en la hoja —las 15 del
    # estado de cuenta— se retira. Sólo si nadie le registró un pago encima.
    for numero, previa in previas.items():
        if abs(float(previa["saldo"] or 0) - float(previa["total"] or 0)) > 0.01:
            res["respetadas"].append(numero)
            continue
        db.ex("DELETE FROM factura_items WHERE factura_id=?", (previa["id"],))
        db.ex("DELETE FROM facturas WHERE id=?", (previa["id"],))
        res["retiradas"] += 1

    res["total"] = round(res["total"], 2)
    res["descuadre"] = round(res["total"] - res["total_escrito"], 2)
    res["cuadra"] = abs(res["descuadre"]) < 1
    db.log(usuario, "importar_cartera", "facturas", str(ruta), str(res))
    return res
