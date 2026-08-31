"""Consecutivos por tipo de documento y año: COT-2026-0001, REM-2026-0001, FE-1..."""
from datetime import date
from . import db

PREFIJOS = {"pedido": "PED", "cotizacion": "COT", "remision": "REM", "factura": "FE"}


def siguiente(tipo: str, anio: int | None = None) -> int:
    anio = anio or date.today().year
    with db.get_db() as con:
        con.execute("INSERT OR IGNORE INTO consecutivos(tipo,anio,ultimo) VALUES(?,?,0)", (tipo, anio))
        con.execute("UPDATE consecutivos SET ultimo=ultimo+1 WHERE tipo=? AND anio=?", (tipo, anio))
        return con.execute("SELECT ultimo FROM consecutivos WHERE tipo=? AND anio=?",
                           (tipo, anio)).fetchone()[0]


def numero(tipo: str) -> str:
    anio = date.today().year
    n = siguiente(tipo, anio)
    if tipo == "factura":
        # La numeración de facturación electrónica la define la resolución DIAN
        prefijo = db.get_config("empresa.dian_prefijo", "FE")
        desde = int(db.get_config("empresa.dian_rango_desde", "1") or 1)
        return f"{prefijo}{desde + n - 1}", desde + n - 1
    return f"{PREFIJOS[tipo]}-{anio}-{n:04d}"
