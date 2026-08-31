"""Configuración central de la aplicación IMATEC S.A.S."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
EXCEL_DIR = DATA_DIR / "excel"
UPLOAD_DIR = DATA_DIR / "uploads"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
DB_PATH = DATA_DIR / "imatec.db"

for _d in (DATA_DIR, EXCEL_DIR, UPLOAD_DIR):
    _d.mkdir(parents=True, exist_ok=True)

SECRET_KEY = os.environ.get("IMATEC_SECRET_KEY", "cambie-esta-clave-en-produccion-imatec-sas")
SESSION_COOKIE = "imatec_session"
SESSION_MAX_AGE = 60 * 60 * 12  # 12 horas

# --- Identidad de marca (extraída del logo oficial en imatecsas.com) ---
BRAND = {
    "amarillo": "#FCEA0B",       # amarillo dominante del logo
    "amarillo_web": "#EDF000",   # acento del sitio actual (Divi)
    "amarillo_oscuro": "#F0D200",
    "negro": "#1B1B1A",          # negro del logo
    "grafito": "#292F33",        # gris oscuro del sitio actual
    "gris": "#9B9B9B",           # gris acero del logo
    "blanco": "#FFFFFF",
}

# --- Datos de la empresa (editables desde /admin/configuracion) ---
EMPRESA_DEFAULT = {
    "razon_social": "IMATEC S.A.S.",
    "nit": "",
    "dv": "",
    "direccion": "Calle 33B # 17C-68",
    "ciudad": "Cali",
    "departamento": "Valle del Cauca",
    "pais": "Colombia",
    "telefono": "+57 321-783-4969",
    "email": "contacto@imatecsas.com",
    "web": "https://imatecsas.com",
    "horario": "Lunes a Sábado de 8:00am a 6:00pm",
    "regimen": "Responsable de IVA",
    "actividad_ciiu": "2599",
    "iva_defecto": "19",
    "validez_cotizacion_dias": "15",
    "plazo_factura_dias": "30",
    # Facturación electrónica DIAN (se llenan cuando la DIAN habilite a la empresa)
    "dian_resolucion": "",
    "dian_prefijo": "FE",
    "dian_rango_desde": "1",
    "dian_rango_hasta": "5000",
    "dian_fecha_resolucion": "",
    "dian_clave_tecnica": "",
    "dian_ambiente": "pruebas",
    "dian_proveedor": "",
}

MONEDA = "COP"
