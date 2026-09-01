"""Configuración central de la aplicación IMATEC S.A.S."""
import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------
#  Dónde viven los datos.
#  En el computador de la oficina: ./data
#  En Railway (o cualquier servidor): la carpeta del disco persistente,
#  que se indica con la variable IMATEC_DATA_DIR (por ejemplo /datos).
#  Es indispensable que apunte a un disco persistente: el sistema de
#  archivos del contenedor se borra en cada despliegue.
# ---------------------------------------------------------------------
DATA_DIR = Path(os.environ.get("IMATEC_DATA_DIR", BASE_DIR / "data")).resolve()
EXCEL_DIR = DATA_DIR / "excel"
UPLOAD_DIR = DATA_DIR / "uploads"          # importaciones y copias de la base
IMAGENES_DIR = DATA_DIR / "imagenes"       # fotos que se suben desde el panel
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
DB_PATH = DATA_DIR / "imatec.db"

for _d in (DATA_DIR, EXCEL_DIR, UPLOAD_DIR, IMAGENES_DIR):
    _d.mkdir(parents=True, exist_ok=True)

EN_PRODUCCION = bool(os.environ.get("RAILWAY_ENVIRONMENT") or
                     os.environ.get("IMATEC_PRODUCCION"))


def _clave_secreta() -> str:
    """Clave con la que se firman las sesiones.

    Prioridad: variable de entorno > clave guardada en el disco persistente >
    clave nueva generada al azar. Nunca se usa una clave que esté en el código
    fuente: cualquiera que lea el repositorio podría falsificar sesiones.
    """
    clave = os.environ.get("IMATEC_SECRET_KEY", "").strip()
    if clave:
        return clave
    archivo = DATA_DIR / ".clave_sesion"
    if archivo.exists():
        guardada = archivo.read_text(encoding="utf-8").strip()
        if guardada:
            return guardada
    nueva = secrets.token_urlsafe(48)
    try:
        archivo.write_text(nueva, encoding="utf-8")
        archivo.chmod(0o600)
    except OSError:
        pass
    return nueva


SECRET_KEY = _clave_secreta()
SESSION_COOKIE = "imatec_session"
SESSION_MAX_AGE = 60 * 60 * 12          # 12 horas
COOKIE_SEGURA = EN_PRODUCCION           # sólo por HTTPS cuando está publicado

# Contraseña del primer administrador. En producción se debe fijar por variable
# de entorno; si no, se genera una al azar y se muestra una sola vez en el log.
ADMIN_EMAIL = os.environ.get("IMATEC_ADMIN_EMAIL", "admin@imatecsas.com")
ADMIN_PASSWORD = os.environ.get("IMATEC_ADMIN_PASSWORD", "")

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
    "direccion": "Calle 33A # 17F-56",
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
