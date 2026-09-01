"""Importa el «LISTADO DE PRECIOS - FERRETERIA INDUSTRIAL» al inventario.

Columnas del archivo: DESCRIPCION | (medida) | UNIDAD | COSTO | IVA | VR. FINAL.
VR. FINAL es siempre COSTO x 1,19, así que COSTO es el valor sin IVA.

Los ítems entran con `publicado = 0`: quedan cargados y listos, pero no se
muestran en el catálogo hasta que alguien confirme que esos valores son de
venta y no de compra. Publicar un precio de costo sería vender sin margen.
"""
import re
import unicodedata
from pathlib import Path

from openpyxl import load_workbook

from . import db

CATEGORIAS = [
    ("TUBERIA", "Tuberías"), ("TUBO", "Tuberías"),
    ("BRIDA", "Accesorios"), ("CODO", "Accesorios"), ("TEE", "Accesorios"),
    ("REDUCCION", "Accesorios"), ("UNION", "Accesorios"), ("NIPLE", "Accesorios"),
    ("TAPON", "Accesorios"), ("ABRAZADERA", "Accesorios"), ("ACOPLE", "Accesorios"),
    ("VALVULA", "Accesorios"), ("CHEQUE", "Accesorios"), ("EMPAQUE", "Accesorios"),
    ("ANGULO", "Acero"), ("LAMINA", "Acero"), ("PLATINA", "Acero"), ("VARILLA", "Acero"),
    ("PERFIL", "Acero"), ("VIGA", "Acero"),
]

MATERIALES = [
    ("AC/INOX 316", "Acero inoxidable"), ("AC/INOX 304", "Acero inoxidable"),
    ("AC/INOX", "Acero inoxidable"), ("INOX", "Acero inoxidable"),
    ("GALVANIZAD", "Galvanizado"), ("HD RANURAD", "Hd ranurado"),
    ("CPVC", "CPVC"), ("PVC SCH 80", "PVC SCH 80"), ("PVC SCH 40", "PVC SCH 40"),
    ("PVC", "PVC SCH 40"), ("A / C", "Acero al carbón"), ("A/C", "Acero al carbón"),
    ("ACERO AL CARBON", "Acero al carbón"),
]


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", str(t or "")).encode("ascii", "ignore").decode()
    return " ".join(t.upper().split())


def _clasificar(desc: str, tabla) -> str:
    d = _norm(desc)
    for clave, valor in tabla:
        if clave in d:
            return valor
    return ""


def _sku(desc: str, medida: str, usados: set) -> str:
    base = _norm(desc)[:26].replace(" ", "-")
    base = re.sub(r"[^A-Z0-9\-]", "", base).strip("-") or "ITEM"
    med = re.sub(r"[^A-Z0-9]", "", _norm(medida))[:6]
    sku = f"{base}-{med}" if med else base
    n, final = 2, sku
    while final in usados:
        final = f"{sku}-{n}"
        n += 1
    usados.add(final)
    return final


def importar_precios(ruta, usuario: str = "listado de precios") -> dict:
    ws = load_workbook(Path(ruta), data_only=True).worksheets[0]
    usados = {r["sku"] for r in db.q("SELECT sku FROM materiales")}
    res = {"nuevos": 0, "actualizados": 0, "omitidos": 0}

    for fila in range(4, ws.max_row + 1):
        desc = ws.cell(fila, 1).value
        costo = ws.cell(fila, 6).value
        if not desc or not isinstance(costo, (int, float)) or costo <= 0:
            res["omitidos"] += 1
            continue

        desc = " ".join(str(desc).split())
        medida = " ".join(str(ws.cell(fila, 4).value or "").split()).replace("*", '"')
        unidad = " ".join(str(ws.cell(fila, 5).value or "").split()) or "Unidades"
        completo = f"{desc} {medida}".strip()

        existente = db.q1("SELECT id FROM materiales WHERE descripcion=?", (completo,))
        if existente:
            db.ex("""UPDATE materiales SET precio_venta=?, costo_unitario=?,
                     actualizado_en=datetime('now','localtime') WHERE id=?""",
                  (round(float(costo)), round(float(costo)), existente["id"]))
            res["actualizados"] += 1
        else:
            db.ex("""INSERT INTO materiales
                     (sku,categoria,material,diametro,descripcion,cantidad,unidad,
                      costo_unitario,precio_venta,publicado,notas)
                     VALUES(?,?,?,?,?,0,?,?,?,0,'Del listado de precios')""",
                  (_sku(desc, medida, usados),
                   _clasificar(desc, CATEGORIAS) or "Otros",
                   _clasificar(desc, MATERIALES),
                   medida, completo, unidad,
                   round(float(costo)), round(float(costo))))
            res["nuevos"] += 1

    db.log(usuario, "importar_precios", "materiales", str(ruta), str(res))
    return res
