"""Carga la cartera real desde «RELACION DE CARTERA IMATEC S.A.S.xlsx».

El archivo trae: cliente, número de factura, valor y fecha de vencimiento
repartida en tres columnas (día, mes, año). Cada fila se convierte en una
factura ya emitida con su saldo pendiente, para que el estado de cuenta del
portal refleje la deuda real y no arranque en cero.

Los nombres del archivo vienen abreviados («TUVACOL», «V A A SOLUCIONES»),
así que se cruzan contra los clientes por coincidencia de nombre normalizado.
Lo que no cruza se reporta en vez de inventarse un cliente.
"""
import difflib
import unicodedata
from datetime import date
from pathlib import Path

from openpyxl import load_workbook

from . import db


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


def importar_cartera(ruta, usuario: str = "relación de cartera") -> dict:
    wb = load_workbook(Path(ruta), data_only=True)
    indice = {_norm(c["razon_social"]): c["id"]
              for c in db.q("SELECT id, razon_social FROM clientes")}
    for c in db.q("SELECT id, nombre_comercial FROM clientes WHERE nombre_comercial<>''"):
        indice.setdefault(_norm(c["nombre_comercial"]), c["id"])

    res = {"creadas": 0, "existentes": 0, "sin_cliente": [], "omitidas": 0, "total": 0.0}

    for ws in wb.worksheets:
        for fila in ws.iter_rows(min_row=1, values_only=True):
            vals = list(fila) + [None] * 10
            nombre, numero, valor = vals[0], vals[4], vals[5]
            dd, mm, aa = vals[6], vals[7], vals[8]
            if not nombre or not isinstance(valor, (int, float)) or valor <= 0:
                res["omitidas"] += 1
                continue
            if not all(isinstance(x, (int, float)) for x in (dd, mm, aa)):
                res["omitidas"] += 1
                continue

            numero = str(numero or "").strip() or f"SIN-NUM-{int(valor)}"
            if not numero.upper().startswith("FEV"):
                numero = f"FEV-{numero}"

            cid = _buscar_cliente(nombre, indice)
            if not cid:
                cid = _crear_cliente_minimo(nombre)
                indice[_norm(nombre)] = cid
                res["sin_cliente"].append(str(nombre).strip())
                res["clientes_creados"] = res.get("clientes_creados", 0) + 1
            if db.q1("SELECT 1 FROM facturas WHERE numero=?", (numero,)):
                res["existentes"] += 1
                continue

            try:
                vence = date(int(aa), int(mm), int(dd)).isoformat()
            except ValueError:
                res["omitidas"] += 1
                continue

            total = round(float(valor), 2)
            base = round(total / 1.19, 2)
            db.ex("""INSERT INTO facturas
                     (numero,prefijo,consecutivo,cliente_id,fecha_emision,fecha_vencimiento,
                      forma_pago,medio_pago,subtotal,descuento,iva,total,saldo,estado,
                      observaciones,elaborado_por)
                     VALUES(?,?,0,?,?,?,'credito','transferencia',?,0,?,?,?,'emitida',
                            'Saldo trasladado de la relación de cartera',?)""",
                  (numero, "FEV", cid, vence, vence, base, round(total - base, 2),
                   total, total, usuario))
            res["creadas"] += 1
            res["total"] += total

    res["total"] = round(res["total"], 2)
    db.log(usuario, "importar_cartera", "facturas", str(ruta), str(res))
    return res
