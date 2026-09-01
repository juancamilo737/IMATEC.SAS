"""Importa los clientes exportados desde Xubio (archivo NXVOrganizacion).

Xubio exporta las organizaciones con nombres de columna propios; aquí se
traducen a los campos que usa IMATEC. Se identifica cada cliente por su NIT,
así que volver a correr la importación actualiza en vez de duplicar.
"""
from pathlib import Path

from openpyxl import load_workbook

from . import db

# columna de Xubio -> significado en IMATEC
CIUDADES = {"VALLE_DEL_CAUCA": "Valle del Cauca", "BOGOTA": "Bogotá D.C.",
            "CUNDINAMARCA": "Cundinamarca", "ANTIOQUIA": "Antioquia",
            "ATLANTICO": "Atlántico", "SANTANDER": "Santander"}


def _texto(v) -> str:
    return " ".join(str(v).split()) if v is not None else ""


def _titulo(v: str) -> str:
    """CALI -> Cali, VALLE_DEL_CAUCA -> Valle del Cauca."""
    v = _texto(v)
    return CIUDADES.get(v, v.replace("_", " ").title() if v.isupper() else v)


def _ciudad(localidad, provincia) -> str:
    """Xubio a veces deja la localidad vacía. Antes se ponía «Cali» por defecto,
    lo que le asignaba mal la ciudad a clientes de Bogotá; mejor dejarla en
    blanco que imprimir una dirección equivocada en una factura."""
    loc = _titulo(localidad)
    if loc:
        return loc
    prov = _texto(provincia).upper()
    return "Bogotá D.C." if prov == "BOGOTA" else ""


def importar_clientes(ruta, usuario: str = "importación Xubio") -> dict:
    wb = load_workbook(Path(ruta), data_only=True)
    ws = wb.worksheets[0]
    cab = {c.value: i for i, c in enumerate(ws[1]) if c.value}

    def col(fila, nombre):
        i = cab.get(nombre)
        return fila[i] if i is not None and i < len(fila) else None

    res = {"nuevos": 0, "actualizados": 0, "omitidos": 0, "errores": []}
    n = db.scalar("SELECT COUNT(*) FROM clientes")

    for fila in ws.iter_rows(min_row=2, values_only=True):
        # Las empresas (PJ) traen «RazonSocial»; las personas naturales (PN),
        # sólo «Nombre». Sin este respaldo se perdían 24 clientes reales.
        es_persona = _texto(col(fila, "TipoDeOrganizacion_Codigo")).upper() == "PN"
        razon = _texto(col(fila, "RazonSocial")) or _texto(col(fila, "Nombre"))
        nit = _texto(col(fila, "CUIT")).replace(".", "").replace("-", "")
        if not razon or not nit:
            res["omitidos"] += 1
            continue
        if razon.lower() == "consumidor final":     # cliente genérico de Xubio
            res["omitidos"] += 1
            continue

        datos = {
            "tipo_documento": "CC" if es_persona else "NIT",
            "documento": nit,
            "dv": _texto(col(fila, "DigitoVerificacionDian")),
            "razon_social": razon,
            "nombre_comercial": _texto(col(fila, "NombreComercial")),
            "email": _texto(col(fila, "Email")).lower(),
            "telefono": _texto(col(fila, "Telefono")),
            "direccion": _texto(col(fila, "DireccionCalle")),
            "ciudad": _ciudad(col(fila, "Localidad_Codigo"), col(fila, "Provincia_Codigo")),
            "departamento": _titulo(col(fila, "Provincia_Codigo")),
            "regimen": ("Responsable de IVA"
                        if _texto(col(fila, "CategoriaFiscal_Codigo")).upper() == "IVA"
                        else "No responsable de IVA"),
            "activo": 1 if _texto(col(fila, "Activo")) in ("1", "True", "") else 0,
        }

        existente = db.q1("SELECT id FROM clientes WHERE documento=?", (nit,))
        if existente:
            db.ex("""UPDATE clientes SET tipo_documento=?,dv=?,razon_social=?,nombre_comercial=?,
                     email=?,telefono=?,direccion=?,ciudad=?,departamento=?,regimen=?,activo=?
                     WHERE id=?""",
                  (datos["tipo_documento"], datos["dv"], datos["razon_social"],
                   datos["nombre_comercial"], datos["email"], datos["telefono"],
                   datos["direccion"], datos["ciudad"], datos["departamento"],
                   datos["regimen"], datos["activo"], existente["id"]))
            res["actualizados"] += 1
        else:
            n += 1
            db.ex("""INSERT INTO clientes(codigo,tipo_documento,documento,dv,razon_social,
                     nombre_comercial,email,telefono,direccion,ciudad,departamento,regimen,activo)
                     VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (f"CL-{n:04d}", datos["tipo_documento"], nit, datos["dv"],
                   datos["razon_social"], datos["nombre_comercial"], datos["email"],
                   datos["telefono"], datos["direccion"], datos["ciudad"],
                   datos["departamento"], datos["regimen"], datos["activo"]))
            res["nuevos"] += 1

    db.log(usuario, "importar_clientes", "clientes", str(ruta), str(res))
    return res
