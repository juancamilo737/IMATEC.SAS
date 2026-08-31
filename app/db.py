"""Capa de acceso a datos (SQLite). Un solo archivo => respaldo = copiar data/imatec.db"""
import sqlite3
from contextlib import contextmanager
from .config import DB_PATH

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS config (
    clave TEXT PRIMARY KEY,
    valor TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    nombre TEXT NOT NULL,
    rol TEXT NOT NULL DEFAULT 'cliente',        -- admin | vendedor | cliente
    cliente_id INTEGER REFERENCES clientes(id),
    activo INTEGER NOT NULL DEFAULT 1,
    creado_en TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    ultimo_acceso TEXT
);

CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT UNIQUE,
    tipo_documento TEXT NOT NULL DEFAULT 'NIT',  -- NIT | CC | CE | PAS
    documento TEXT NOT NULL,
    dv TEXT DEFAULT '',
    razon_social TEXT NOT NULL,
    nombre_comercial TEXT DEFAULT '',
    contacto TEXT DEFAULT '',
    email TEXT DEFAULT '',
    telefono TEXT DEFAULT '',
    direccion TEXT DEFAULT '',
    ciudad TEXT DEFAULT 'Cali',
    departamento TEXT DEFAULT 'Valle del Cauca',
    regimen TEXT DEFAULT 'Responsable de IVA',
    responsabilidad_fiscal TEXT DEFAULT 'O-1',
    condicion_pago INTEGER NOT NULL DEFAULT 30,   -- días de plazo
    cupo_credito REAL NOT NULL DEFAULT 0,
    descuento_pct REAL NOT NULL DEFAULT 0,
    notas TEXT DEFAULT '',
    activo INTEGER NOT NULL DEFAULT 1,
    creado_en TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS ix_clientes_doc ON clientes(documento);

CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    descripcion TEXT DEFAULT '',
    orden INTEGER NOT NULL DEFAULT 0,
    activo INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT UNIQUE NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    nombre TEXT NOT NULL,
    categoria_id INTEGER NOT NULL REFERENCES categorias(id),
    descripcion TEXT DEFAULT '',
    especificaciones TEXT DEFAULT '',
    material TEXT DEFAULT 'Acero inoxidable 304',
    unidad TEXT NOT NULL DEFAULT 'UND',
    precio REAL NOT NULL DEFAULT 0,
    iva_pct REAL NOT NULL DEFAULT 19,
    a_pedido INTEGER NOT NULL DEFAULT 1,          -- 1 = fabricación bajo medida
    dias_entrega INTEGER NOT NULL DEFAULT 15,
    imagen TEXT DEFAULT '',
    destacado INTEGER NOT NULL DEFAULT 0,
    activo INTEGER NOT NULL DEFAULT 1,
    grupo_sku TEXT DEFAULT '',        -- prefijo de SKU: publica una familia del inventario
    creado_en TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS ix_productos_cat ON productos(categoria_id);

CREATE TABLE IF NOT EXISTS inventario (
    producto_id INTEGER PRIMARY KEY REFERENCES productos(id) ON DELETE CASCADE,
    stock REAL NOT NULL DEFAULT 0,
    stock_minimo REAL NOT NULL DEFAULT 0,
    ubicacion TEXT DEFAULT 'Bodega principal',
    costo_promedio REAL NOT NULL DEFAULT 0,
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS movimientos_inventario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL REFERENCES productos(id),
    tipo TEXT NOT NULL,                            -- entrada | salida | ajuste
    cantidad REAL NOT NULL,
    saldo REAL NOT NULL DEFAULT 0,
    costo_unitario REAL NOT NULL DEFAULT 0,
    motivo TEXT DEFAULT '',
    documento TEXT DEFAULT '',
    usuario TEXT DEFAULT '',
    fecha TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS ix_mov_prod ON movimientos_inventario(producto_id);

-- Solicitudes que entran desde la web (carrito del cliente)
CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT UNIQUE NOT NULL,
    cliente_id INTEGER REFERENCES clientes(id),
    nombre_contacto TEXT DEFAULT '',
    email TEXT DEFAULT '',
    telefono TEXT DEFAULT '',
    empresa TEXT DEFAULT '',
    estado TEXT NOT NULL DEFAULT 'nuevo',          -- nuevo | en_cotizacion | cotizado | cerrado | anulado
    notas TEXT DEFAULT '',
    total_estimado REAL NOT NULL DEFAULT 0,
    fecha TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS pedido_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
    producto_id INTEGER REFERENCES productos(id),
    material_id INTEGER REFERENCES materiales(id),
    descripcion TEXT NOT NULL,
    cantidad REAL NOT NULL DEFAULT 1,
    unidad TEXT DEFAULT 'UND',
    precio REAL NOT NULL DEFAULT 0,
    observacion TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS cotizaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT UNIQUE NOT NULL,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    pedido_id INTEGER REFERENCES pedidos(id),
    fecha TEXT NOT NULL DEFAULT (date('now','localtime')),
    validez_dias INTEGER NOT NULL DEFAULT 15,
    estado TEXT NOT NULL DEFAULT 'borrador',       -- borrador|enviada|aprobada|rechazada|vencida
    subtotal REAL NOT NULL DEFAULT 0,
    descuento REAL NOT NULL DEFAULT 0,
    iva REAL NOT NULL DEFAULT 0,
    total REAL NOT NULL DEFAULT 0,
    tiempo_entrega TEXT DEFAULT '15 días hábiles',
    forma_pago TEXT DEFAULT '50% anticipo, 50% contra entrega',
    condiciones TEXT DEFAULT '',
    notas TEXT DEFAULT '',
    elaborado_por TEXT DEFAULT '',
    creado_en TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS cotizacion_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cotizacion_id INTEGER NOT NULL REFERENCES cotizaciones(id) ON DELETE CASCADE,
    producto_id INTEGER REFERENCES productos(id),
    orden INTEGER NOT NULL DEFAULT 0,
    descripcion TEXT NOT NULL,
    especificaciones TEXT DEFAULT '',
    cantidad REAL NOT NULL DEFAULT 1,
    unidad TEXT DEFAULT 'UND',
    precio REAL NOT NULL DEFAULT 0,
    descuento_pct REAL NOT NULL DEFAULT 0,
    iva_pct REAL NOT NULL DEFAULT 19,
    total REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS remisiones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT UNIQUE NOT NULL,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    cotizacion_id INTEGER REFERENCES cotizaciones(id),
    fecha TEXT NOT NULL DEFAULT (date('now','localtime')),
    estado TEXT NOT NULL DEFAULT 'pendiente',      -- pendiente|despachada|entregada|anulada
    direccion_entrega TEXT DEFAULT '',
    ciudad_entrega TEXT DEFAULT '',
    transportador TEXT DEFAULT '',
    placa TEXT DEFAULT '',
    conductor TEXT DEFAULT '',
    recibido_por TEXT DEFAULT '',
    fecha_entrega TEXT DEFAULT '',
    orden_compra TEXT DEFAULT '',
    observaciones TEXT DEFAULT '',
    elaborado_por TEXT DEFAULT '',
    creado_en TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS remision_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    remision_id INTEGER NOT NULL REFERENCES remisiones(id) ON DELETE CASCADE,
    producto_id INTEGER REFERENCES productos(id),
    orden INTEGER NOT NULL DEFAULT 0,
    descripcion TEXT NOT NULL,
    cantidad REAL NOT NULL DEFAULT 1,
    unidad TEXT DEFAULT 'UND',
    precio REAL NOT NULL DEFAULT 0,
    descuento_pct REAL NOT NULL DEFAULT 0,
    iva_pct REAL NOT NULL DEFAULT 19,
    observacion TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS facturas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT UNIQUE NOT NULL,
    prefijo TEXT DEFAULT 'FE',
    consecutivo INTEGER NOT NULL DEFAULT 0,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id),
    cotizacion_id INTEGER REFERENCES cotizaciones(id),
    remision_id INTEGER REFERENCES remisiones(id),
    fecha_emision TEXT NOT NULL DEFAULT (date('now','localtime')),
    fecha_vencimiento TEXT DEFAULT '',
    forma_pago TEXT NOT NULL DEFAULT 'credito',    -- contado | credito
    medio_pago TEXT NOT NULL DEFAULT 'transferencia',
    subtotal REAL NOT NULL DEFAULT 0,
    descuento REAL NOT NULL DEFAULT 0,
    iva REAL NOT NULL DEFAULT 0,
    total REAL NOT NULL DEFAULT 0,
    saldo REAL NOT NULL DEFAULT 0,
    estado TEXT NOT NULL DEFAULT 'borrador',       -- borrador|emitida|enviada_dian|aceptada|pagada|anulada
    cufe TEXT DEFAULT '',
    qr_data TEXT DEFAULT '',
    resolucion_dian TEXT DEFAULT '',
    orden_compra TEXT DEFAULT '',
    observaciones TEXT DEFAULT '',
    elaborado_por TEXT DEFAULT '',
    creado_en TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS factura_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    factura_id INTEGER NOT NULL REFERENCES facturas(id) ON DELETE CASCADE,
    producto_id INTEGER REFERENCES productos(id),
    orden INTEGER NOT NULL DEFAULT 0,
    descripcion TEXT NOT NULL,
    especificaciones TEXT DEFAULT '',
    cantidad REAL NOT NULL DEFAULT 1,
    unidad TEXT DEFAULT 'UND',
    precio REAL NOT NULL DEFAULT 0,
    descuento_pct REAL NOT NULL DEFAULT 0,
    iva_pct REAL NOT NULL DEFAULT 19,
    total REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS pagos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    factura_id INTEGER NOT NULL REFERENCES facturas(id) ON DELETE CASCADE,
    fecha TEXT NOT NULL DEFAULT (date('now','localtime')),
    valor REAL NOT NULL DEFAULT 0,
    medio TEXT DEFAULT 'transferencia',
    referencia TEXT DEFAULT '',
    registrado_por TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS consecutivos (
    tipo TEXT NOT NULL,
    anio INTEGER NOT NULL,
    ultimo INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (tipo, anio)
);

CREATE TABLE IF NOT EXISTS bitacora (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    usuario TEXT DEFAULT '',
    accion TEXT NOT NULL,
    entidad TEXT DEFAULT '',
    referencia TEXT DEFAULT '',
    detalle TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS mensajes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    nombre TEXT NOT NULL,
    email TEXT DEFAULT '',
    telefono TEXT DEFAULT '',
    asunto TEXT DEFAULT '',
    mensaje TEXT NOT NULL,
    leido INTEGER NOT NULL DEFAULT 0
);
"""


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH, timeout=15, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con


@contextmanager
def get_db():
    con = connect()
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def init_db() -> None:
    """Crea todas las tablas (idempotente)."""
    con = connect()
    try:
        con.executescript(SCHEMA)
        con.commit()
    finally:
        con.close()


# ---------- helpers ----------
def q(sql: str, params=()) -> list:
    with get_db() as con:
        return [dict(r) for r in con.execute(sql, params).fetchall()]


def q1(sql: str, params=()):
    with get_db() as con:
        r = con.execute(sql, params).fetchone()
        return dict(r) if r else None


def ex(sql: str, params=()) -> int:
    with get_db() as con:
        cur = con.execute(sql, params)
        return cur.lastrowid


def scalar(sql: str, params=(), default=0):
    with get_db() as con:
        r = con.execute(sql, params).fetchone()
        if not r or r[0] is None:
            return default
        return r[0]


def get_config(clave: str, default: str = "") -> str:
    r = q1("SELECT valor FROM config WHERE clave=?", (clave,))
    return r["valor"] if r else default


def set_config(clave: str, valor: str) -> None:
    ex("INSERT INTO config(clave,valor) VALUES(?,?) "
       "ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor", (clave, str(valor)))


def empresa() -> dict:
    from .config import EMPRESA_DEFAULT
    datos = dict(EMPRESA_DEFAULT)
    for row in q("SELECT clave,valor FROM config"):
        if row["clave"].startswith("empresa."):
            datos[row["clave"][8:]] = row["valor"]
    return datos


def log(usuario: str, accion: str, entidad: str = "", referencia: str = "", detalle: str = "") -> None:
    ex("INSERT INTO bitacora(usuario,accion,entidad,referencia,detalle) VALUES(?,?,?,?,?)",
       (usuario, accion, entidad, referencia, detalle))


# =====================================================================
# Inventario de MATERIA PRIMA — espejo del Excel "Inventario Imatec"
# Columnas: ID Artículo | Categoría | Material | Diametro | Descripción
#           | Cantidad | Unidad | Estado | Notas
# =====================================================================
SCHEMA_MATERIALES = """
CREATE TABLE IF NOT EXISTS materiales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT UNIQUE NOT NULL,                     -- ID Artículo
    categoria TEXT NOT NULL DEFAULT 'Tuberías',
    material TEXT NOT NULL DEFAULT '',
    diametro TEXT DEFAULT '',
    descripcion TEXT NOT NULL,
    cantidad REAL NOT NULL DEFAULT 0,
    unidad TEXT NOT NULL DEFAULT 'Metros',
    notas TEXT DEFAULT '',
    stock_minimo REAL NOT NULL DEFAULT 0,
    ubicacion TEXT DEFAULT 'Bodega principal',
    costo_unitario REAL NOT NULL DEFAULT 0,
    precio_venta REAL NOT NULL DEFAULT 0,
    publicado INTEGER NOT NULL DEFAULT 1,
    proveedor TEXT DEFAULT '',
    activo INTEGER NOT NULL DEFAULT 1,
    creado_en TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    actualizado_en TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS ix_mat_cat ON materiales(categoria);
CREATE INDEX IF NOT EXISTS ix_mat_material ON materiales(material);

CREATE TABLE IF NOT EXISTS movimientos_material (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    material_id INTEGER NOT NULL REFERENCES materiales(id) ON DELETE CASCADE,
    tipo TEXT NOT NULL,                            -- entrada | salida | ajuste
    cantidad REAL NOT NULL,
    saldo REAL NOT NULL DEFAULT 0,
    costo_unitario REAL NOT NULL DEFAULT 0,
    motivo TEXT DEFAULT '',
    documento TEXT DEFAULT '',
    usuario TEXT DEFAULT '',
    fecha TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS ix_movmat ON movimientos_material(material_id);

-- Listas desplegables del Excel (editables desde el dashboard)
CREATE TABLE IF NOT EXISTS listas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lista TEXT NOT NULL,          -- categoria | material | diametro | unidad
    valor TEXT NOT NULL,
    orden INTEGER NOT NULL DEFAULT 0,
    UNIQUE(lista, valor)
);
"""

# Valores exactos de las validaciones de datos del Excel actual de IMATEC
LISTAS_INICIALES = {
    "categoria": ["Tuberías", "Accesorios", "Acero", "Otros"],
    "material": ["Acero al carbón", "Acero inoxidable", "Galvanizado", "Hd ranurado",
                 "PVC SCH 40", "PVC SCH 80", "CPVC"],
    "diametro": ['1/4"', '3/8"', '1/2"', '3/4"', '1"', '1 1/4"', '1 1/2"', '2"', '2 1/2"',
                 '3"', '4"', '5"', '6"', '7"', '8"', '9"', '10"'],
    "unidad": ["Metros", "Unidades", "Kilos", "Láminas", "Litros", "Galones", "Rollos", "Global"],
}


def estado_material(cantidad: float) -> str:
    """Misma regla del Excel: =IF(G>0,"Disponible","No disponible")"""
    return "Disponible" if (cantidad or 0) > 0 else "No disponible"


def init_materiales() -> None:
    con = connect()
    try:
        con.executescript(SCHEMA_MATERIALES)
        for lista, valores in LISTAS_INICIALES.items():
            for i, v in enumerate(valores):
                con.execute("INSERT OR IGNORE INTO listas(lista,valor,orden) VALUES(?,?,?)",
                            (lista, v, i))
        con.commit()
    finally:
        con.close()


def opciones(lista: str) -> list:
    return [r["valor"] for r in q(
        "SELECT valor FROM listas WHERE lista=? ORDER BY orden, valor", (lista,))]
