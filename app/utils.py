"""Utilidades de formato y cálculo."""
import re, unicodedata
from datetime import date, datetime, timedelta

MESES = ["enero","febrero","marzo","abril","mayo","junio","julio",
         "agosto","septiembre","octubre","noviembre","diciembre"]


def slugify(texto: str) -> str:
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return t or "item"


def cop(valor) -> str:
    """Formato moneda colombiana: $ 1.234.567"""
    try:
        v = float(valor or 0)
    except (TypeError, ValueError):
        return "$ 0"
    entero = f"{abs(v):,.0f}".replace(",", ".")
    return ("-" if v < 0 else "") + f"$ {entero}"


def num(valor, dec=2) -> str:
    try:
        v = float(valor or 0)
    except (TypeError, ValueError):
        return "0"
    s = f"{v:,.{dec}f}".replace(",", "@").replace(".", ",").replace("@", ".")
    return s.rstrip("0").rstrip(",") if dec and "," in s else s


def fecha_larga(f) -> str:
    d = parse_fecha(f)
    return f"{d.day} de {MESES[d.month-1]} de {d.year}" if d else ""


def parse_fecha(f):
    if isinstance(f, (date, datetime)):
        return f.date() if isinstance(f, datetime) else f
    if not f:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(f)[:19], fmt).date()
        except ValueError:
            continue
    return None


def sumar_dias(f, dias: int) -> str:
    d = parse_fecha(f) or date.today()
    return (d + timedelta(days=int(dias or 0))).isoformat()


def calcular_totales(items, descuento_global=0.0):
    """items: lista de dicts con cantidad, precio, descuento_pct, iva_pct."""
    subtotal = iva = 0.0
    for it in items:
        cant = float(it.get("cantidad") or 0)
        precio = float(it.get("precio") or 0)
        desc = float(it.get("descuento_pct") or 0)
        ivap = float(it.get("iva_pct") or 0)
        base = cant * precio * (1 - desc / 100.0)
        it["total"] = round(base, 2)
        subtotal += base
        iva += base * ivap / 100.0
    subtotal = round(subtotal, 2)
    descuento_global = round(float(descuento_global or 0), 2)
    base_final = subtotal - descuento_global
    if subtotal > 0 and descuento_global:
        iva = iva * (base_final / subtotal)
    iva = round(iva, 2)
    return {"subtotal": subtotal, "descuento": descuento_global,
            "iva": iva, "total": round(base_final + iva, 2)}


UNIDADES = ["", "UN", "DOS", "TRES", "CUATRO", "CINCO", "SEIS", "SIETE", "OCHO", "NUEVE",
            "DIEZ", "ONCE", "DOCE", "TRECE", "CATORCE", "QUINCE", "DIECISÉIS", "DIECISIETE",
            "DIECIOCHO", "DIECINUEVE", "VEINTE"]
DECENAS = ["", "", "VEINTI", "TREINTA", "CUARENTA", "CINCUENTA", "SESENTA", "SETENTA",
           "OCHENTA", "NOVENTA"]
CENTENAS = ["", "CIENTO", "DOSCIENTOS", "TRESCIENTOS", "CUATROCIENTOS", "QUINIENTOS",
            "SEISCIENTOS", "SETECIENTOS", "OCHOCIENTOS", "NOVECIENTOS"]


def _c(n: int) -> str:
    if n == 0: return ""
    if n <= 20: return UNIDADES[n]
    if n < 100:
        d, u = divmod(n, 10)
        if d == 2: return "VEINTI" + UNIDADES[u].lower().upper() if u else "VEINTE"
        return DECENAS[d] + (" Y " + UNIDADES[u] if u else "")
    if n == 100: return "CIEN"
    c, r = divmod(n, 100)
    return CENTENAS[c] + (" " + _c(r) if r else "")


def numero_a_letras(valor) -> str:
    """Requisito DIAN: el total de la factura en letras."""
    n = int(round(float(valor or 0)))
    if n == 0: return "CERO PESOS M/CTE"
    partes = []
    millones, resto = divmod(n, 1_000_000)
    miles, unidades = divmod(resto, 1000)
    if millones:
        partes.append("UN MILLÓN" if millones == 1 else f"{_c(millones)} MILLONES")
    if miles:
        partes.append("MIL" if miles == 1 else f"{_c(miles)} MIL")
    if unidades:
        partes.append(_c(unidades))
    return " ".join(partes) + " PESOS M/CTE"
