"""
Respaldo en Excel — dos archivos, tal como los pidió IMATEC:

1. CONTROL_IMATEC.xlsx  -> "imagen a seguir": réplica exacta del formato que la empresa
   ya maneja a mano (hoja 'Inventario Imatec' con su mismo título, cabeceras, fuentes,
   colores, listas desplegables y la columna Estado calculada por fórmula), más las
   hojas de Clientes, Cotizaciones, Remisiones, Facturas, Despachos y Kardex.

2. RESPALDO_IMATEC.xlsx -> volcado técnico completo de la base de datos, una hoja por
   tabla. Sirve para reconstruir todo si algo falla.
"""
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.formula import ArrayFormula

from . import db
from .config import EXCEL_DIR

# ---- Estilos tomados del archivo original de IMATEC ----
FUENTE_TITULO = Font(name="Montserrat", size=24, bold=True, color="FF999999")
FILL_TITULO = PatternFill("solid", fgColor="FFF3F3F3")
FUENTE_CAB = Font(name="Montserrat", size=11, bold=True, color="FFFFD966")
FILL_CAB = PatternFill("solid", fgColor="FF666666")
FUENTE_DATO = Font(name="Roboto", size=10, color="FF181C1F")
CENTRO = Alignment(horizontal="center", vertical="center")
IZQ = Alignment(horizontal="left", vertical="center")
DER = Alignment(horizontal="right", vertical="center")
BORDE = Border(*[Side(style="thin", color="FFD9D9D9")] * 4)

VERDE = PatternFill("solid", fgColor="FFD9EAD3")
ROJO = PatternFill("solid", fgColor="FFF4CCCC")
AMARILLO = PatternFill("solid", fgColor="FFFFF2CC")

COLS_INVENTARIO = ["ID Artículo", "Categoría", "Material", "Diametro", "Descripción",
                   "Cantidad", "Unidad", "Estado", "Notas"]

RUTA_CONTROL = EXCEL_DIR / "CONTROL_IMATEC.xlsx"
RUTA_RESPALDO = EXCEL_DIR / "RESPALDO_IMATEC.xlsx"


# =====================================================================
#  IMPORTAR el inventario que la empresa ya tiene en Excel
# =====================================================================
def importar_inventario(ruta, usuario: str = "importación") -> dict:
    """Lee un Excel con el formato de IMATEC y carga/actualiza los materiales.
    Devuelve un resumen {nuevos, actualizados, omitidos, errores}."""
    wb = load_workbook(ruta, data_only=True)
    ws = wb["Inventario Imatec"] if "Inventario Imatec" in wb.sheetnames else wb.worksheets[0]

    # Localiza la fila de cabecera buscando "ID Artículo" (tolera títulos arriba)
    fila_cab, col_ini = None, 1
    for fila in ws.iter_rows(min_row=1, max_row=min(ws.max_row, 20)):
        for celda in fila:
            if isinstance(celda.value, str) and celda.value.strip().lower() == "id artículo":
                fila_cab, col_ini = celda.row, celda.column
                break
        if fila_cab:
            break
    if not fila_cab:
        return {"error": "No se encontró la columna 'ID Artículo' en el archivo."}

    cabeceras = {}
    for i in range(9):
        v = ws.cell(row=fila_cab, column=col_ini + i).value
        if isinstance(v, str):
            cabeceras[v.strip().lower()] = col_ini + i

    def val(fila, nombre):
        c = cabeceras.get(nombre)
        return ws.cell(row=fila, column=c).value if c else None

    res = {"nuevos": 0, "actualizados": 0, "omitidos": 0, "errores": []}
    for fila in range(fila_cab + 1, ws.max_row + 1):
        sku = val(fila, "id artículo")
        desc = val(fila, "descripción")
        if not sku and not desc:
            continue
        sku = str(sku).strip() if sku else None
        if not sku:
            res["omitidos"] += 1
            continue
        try:
            cantidad = float(val(fila, "cantidad") or 0)
        except (TypeError, ValueError):
            cantidad = 0.0
        datos = (
            str(val(fila, "categoría") or "Otros").strip(),
            str(val(fila, "material") or "").strip(),
            str(val(fila, "diametro") or "").strip(),
            str(desc or sku).strip(),
            cantidad,
            str(val(fila, "unidad") or "Unidades").strip(),
            str(val(fila, "notas") or "").strip(),
        )
        existente = db.q1("SELECT id, cantidad FROM materiales WHERE sku=?", (sku,))
        if existente:
            db.ex("""UPDATE materiales SET categoria=?,material=?,diametro=?,descripcion=?,
                     cantidad=?,unidad=?,notas=?,actualizado_en=datetime('now','localtime')
                     WHERE id=?""", (*datos, existente["id"]))
            if abs(float(existente["cantidad"] or 0) - cantidad) > 1e-9:
                _mov(existente["id"], "ajuste", cantidad - float(existente["cantidad"] or 0),
                     cantidad, "Importación de Excel", usuario)
            res["actualizados"] += 1
        else:
            mid = db.ex("""INSERT INTO materiales
                           (sku,categoria,material,diametro,descripcion,cantidad,unidad,notas)
                           VALUES(?,?,?,?,?,?,?,?)""", (sku, *datos))
            if cantidad:
                _mov(mid, "entrada", cantidad, cantidad, "Saldo inicial (importación)", usuario)
            res["nuevos"] += 1
            _asegurar_lista("categoria", datos[0])
            _asegurar_lista("material", datos[1])
            _asegurar_lista("diametro", datos[2])
            _asegurar_lista("unidad", datos[5])
    db.log(usuario, "importar_inventario", "materiales", str(ruta), str(res))
    return res


def _asegurar_lista(lista: str, valor: str) -> None:
    if valor:
        db.ex("INSERT OR IGNORE INTO listas(lista,valor,orden) VALUES(?,?,99)", (lista, valor))


def _mov(material_id, tipo, cantidad, saldo, motivo, usuario, documento=""):
    db.ex("""INSERT INTO movimientos_material
             (material_id,tipo,cantidad,saldo,motivo,documento,usuario)
             VALUES(?,?,?,?,?,?,?)""",
          (material_id, tipo, cantidad, saldo, motivo, documento, usuario))


# =====================================================================
#  EXPORTAR — archivo CONTROL (formato de la empresa)
# =====================================================================
def _hoja_inventario(wb: Workbook) -> None:
    ws = wb.create_sheet("Inventario Imatec")
    ws.sheet_view.showGridLines = False

    ws["C2"] = "Inventario de Imatec SAS"
    ws["C2"].font = FUENTE_TITULO
    ws["C2"].fill = FILL_TITULO
    ws.row_dimensions[2].height = 34

    for i, texto in enumerate(COLS_INVENTARIO):
        c = ws.cell(row=4, column=2 + i, value=texto)
        c.font, c.fill, c.alignment, c.border = FUENTE_CAB, FILL_CAB, CENTRO, BORDE
    ws.row_dimensions[4].height = 22

    filas = db.q("""SELECT sku,categoria,material,diametro,descripcion,cantidad,unidad,notas
                    FROM materiales WHERE activo=1
                    ORDER BY categoria, material, id""")
    r = 5
    for m in filas:
        valores = [m["sku"], m["categoria"], m["material"], m["diametro"], m["descripcion"],
                   (m["cantidad"] if m["cantidad"] else None), m["unidad"], None, m["notas"]]
        for i, v in enumerate(valores):
            c = ws.cell(row=r, column=2 + i, value=v)
            c.font, c.border = FUENTE_DATO, BORDE
            c.alignment = DER if i == 5 else IZQ
        # Estado: misma fórmula del archivo original de IMATEC
        ws.cell(row=r, column=9).value = f'=IF(ISBLANK(B{r}),"",IF(G{r}>0,"Disponible","No disponible"))'
        r += 1

    ultima = max(r - 1, 5)
    tope = max(ultima + 200, 1002)          # filas libres para seguir agregando a mano
    for fila in range(r, tope + 1):
        ws.cell(row=fila, column=9).value = \
            f'=IF(ISBLANK(B{fila}),"",IF(G{fila}>0,"Disponible","No disponible"))'
        for col in range(2, 11):
            ws.cell(row=fila, column=col).border = BORDE

    # Listas desplegables idénticas a las del archivo original
    def dv(lista, rango):
        vals = db.opciones(lista)
        if not vals:
            return
        formula = '"' + ",".join(v.replace('"', '""') for v in vals) + '"'
        if len(formula) > 255:
            return
        v = DataValidation(type="list", formula1=formula, allow_blank=True)
        ws.add_data_validation(v)
        v.add(rango)

    dv("categoria", f"C5:C{tope}")
    dv("material", f"D5:D{tope}")
    dv("diametro", f"E5:E{tope}")
    dv("unidad", f"H5:H{tope}")

    ws.conditional_formatting.add(
        f"I5:I{tope}", CellIsRule(operator="equal", formula=['"Disponible"'], fill=VERDE))
    ws.conditional_formatting.add(
        f"I5:I{tope}", CellIsRule(operator="equal", formula=['"No disponible"'], fill=ROJO))

    for col, ancho in zip("ABCDEFGHIJ", [2.8, 19.6, 19.9, 18.9, 12, 31.4, 10.1, 12, 15.1, 25.1]):
        ws.column_dimensions[col].width = ancho
    ws.freeze_panes = "B5"
    ws.auto_filter.ref = f"B4:J{ultima}"


def _tabla(wb: Workbook, titulo: str, cabeceras: list, filas: list,
           anchos: list | None = None, formatos: dict | None = None):
    ws = wb.create_sheet(titulo[:31])
    ws.sheet_view.showGridLines = False
    ws["B2"] = titulo
    ws["B2"].font = Font(name="Montserrat", size=18, bold=True, color="FF999999")
    ws["B2"].fill = FILL_TITULO
    ws.row_dimensions[2].height = 28
    for i, h in enumerate(cabeceras):
        c = ws.cell(row=4, column=2 + i, value=h)
        c.font, c.fill, c.alignment, c.border = FUENTE_CAB, FILL_CAB, CENTRO, BORDE
    ws.row_dimensions[4].height = 22
    for r, fila in enumerate(filas, start=5):
        for i, v in enumerate(fila):
            c = ws.cell(row=r, column=2 + i, value=v)
            c.font, c.border = FUENTE_DATO, BORDE
            c.alignment = DER if isinstance(v, (int, float)) else IZQ
            if formatos and i in formatos:
                c.number_format = formatos[i]
    ws.column_dimensions["A"].width = 2.8
    for i, _ in enumerate(cabeceras):
        letra = get_column_letter(2 + i)
        ws.column_dimensions[letra].width = (anchos[i] if anchos and i < len(anchos) else 18)
    ws.freeze_panes = "B5"
    if filas:
        ws.auto_filter.ref = f"B4:{get_column_letter(1+len(cabeceras))}{4+len(filas)}"
    return ws


MONEDA_FMT = '"$" #,##0'


def exportar_control() -> Path:
    wb = Workbook()
    wb.remove(wb.active)
    _hoja_inventario(wb)

    _tabla(wb, "Clientes",
           ["Código", "Documento", "Razón social", "Contacto", "Teléfono", "Email",
            "Ciudad", "Dirección", "Plazo (días)", "Cupo crédito", "Estado"],
           [[c["codigo"], f'{c["tipo_documento"]} {c["documento"]}', c["razon_social"],
             c["contacto"], c["telefono"], c["email"], c["ciudad"], c["direccion"],
             c["condicion_pago"], c["cupo_credito"], "Activo" if c["activo"] else "Inactivo"]
            for c in db.q("SELECT * FROM clientes ORDER BY razon_social")],
           [12, 18, 34, 22, 16, 26, 14, 30, 12, 16, 10], {9: MONEDA_FMT})

    _tabla(wb, "Cotizaciones",
           ["Número", "Fecha", "Cliente", "Estado", "Válida hasta", "Subtotal", "IVA",
            "Total", "Elaborado por"],
           [[c["numero"], c["fecha"], c["razon_social"], c["estado"].capitalize(),
             c["vence"], c["subtotal"], c["iva"], c["total"], c["elaborado_por"]]
            for c in db.q("""SELECT co.*, cl.razon_social,
                             date(co.fecha, '+'||co.validez_dias||' day') AS vence
                             FROM cotizaciones co JOIN clientes cl ON cl.id=co.cliente_id
                             ORDER BY co.id DESC""")],
           [16, 12, 34, 14, 14, 16, 14, 16, 20], {5: MONEDA_FMT, 6: MONEDA_FMT, 7: MONEDA_FMT})

    _tabla(wb, "Remisiones",
           ["Número", "Fecha", "Cliente", "Cotización", "Estado", "Dirección entrega",
            "Transportador", "Placa", "Recibido por", "Fecha entrega"],
           [[r["numero"], r["fecha"], r["razon_social"], r["cot"] or "", r["estado"].capitalize(),
             r["direccion_entrega"], r["transportador"], r["placa"], r["recibido_por"],
             r["fecha_entrega"]]
            for r in db.q("""SELECT re.*, cl.razon_social, co.numero AS cot
                             FROM remisiones re JOIN clientes cl ON cl.id=re.cliente_id
                             LEFT JOIN cotizaciones co ON co.id=re.cotizacion_id
                             ORDER BY re.id DESC""")],
           [16, 12, 32, 16, 14, 30, 20, 12, 22, 14])

    _tabla(wb, "Facturas",
           ["Número", "Fecha", "Vence", "Cliente", "NIT", "Estado", "Subtotal", "IVA",
            "Total", "Pagado", "Saldo", "CUFE"],
           [[f["numero"], f["fecha_emision"], f["fecha_vencimiento"], f["razon_social"],
             f["documento"], f["estado"].replace("_", " ").capitalize(), f["subtotal"],
             f["iva"], f["total"], (f["total"] or 0) - (f["saldo"] or 0), f["saldo"], f["cufe"]]
            for f in db.q("""SELECT fa.*, cl.razon_social, cl.documento
                             FROM facturas fa JOIN clientes cl ON cl.id=fa.cliente_id
                             ORDER BY fa.id DESC""")],
           [14, 12, 12, 32, 16, 14, 15, 13, 15, 15, 15, 40],
           {6: MONEDA_FMT, 7: MONEDA_FMT, 8: MONEDA_FMT, 9: MONEDA_FMT, 10: MONEDA_FMT})

    _tabla(wb, "Despachos",
           ["Remisión", "Fecha", "Cliente", "Producto", "Cantidad", "Unidad", "Estado",
            "Transportador", "Recibido por"],
           [[d["numero"], d["fecha"], d["razon_social"], d["descripcion"], d["cantidad"],
             d["unidad"], d["estado"].capitalize(), d["transportador"], d["recibido_por"]]
            for d in db.q("""SELECT re.numero, re.fecha, re.estado, re.transportador,
                             re.recibido_por, cl.razon_social, ri.descripcion, ri.cantidad,
                             ri.unidad FROM remision_items ri
                             JOIN remisiones re ON re.id=ri.remision_id
                             JOIN clientes cl ON cl.id=re.cliente_id
                             ORDER BY re.id DESC, ri.orden""")],
           [16, 12, 30, 40, 12, 12, 14, 20, 22])

    _tabla(wb, "Kardex Materiales",
           ["Fecha", "ID Artículo", "Descripción", "Movimiento", "Cantidad", "Saldo",
            "Motivo", "Documento", "Usuario"],
           [[m["fecha"], m["sku"], m["descripcion"], m["tipo"].capitalize(), m["cantidad"],
             m["saldo"], m["motivo"], m["documento"], m["usuario"]]
            for m in db.q("""SELECT mm.*, ma.sku, ma.descripcion
                             FROM movimientos_material mm
                             JOIN materiales ma ON ma.id=mm.material_id
                             ORDER BY mm.id DESC LIMIT 5000""")],
           [18, 18, 34, 14, 12, 12, 28, 18, 20])

    _tabla(wb, "Catálogo Web",
           ["SKU", "Producto", "Categoría", "Material", "Precio", "IVA %", "Días entrega",
            "Publicado"],
           [[p["sku"], p["nombre"], p["categoria"], p["material"], p["precio"], p["iva_pct"],
             p["dias_entrega"], "Sí" if p["activo"] else "No"]
            for p in db.q("""SELECT p.*, c.nombre AS categoria FROM productos p
                             JOIN categorias c ON c.id=p.categoria_id
                             ORDER BY c.orden, p.sku""")],
           [12, 42, 24, 26, 16, 9, 13, 11], {4: MONEDA_FMT})

    portada = wb.create_sheet("Resumen", 0)
    portada.sheet_view.showGridLines = False
    portada["B2"] = "IMATEC S.A.S. — Control operativo"
    portada["B2"].font = FUENTE_TITULO
    portada["B2"].fill = FILL_TITULO
    resumen = [
        ("Generado", datetime.now().strftime("%d/%m/%Y %I:%M %p")),
        ("Materiales en inventario", db.scalar("SELECT COUNT(*) FROM materiales WHERE activo=1")),
        ("Materiales disponibles", db.scalar("SELECT COUNT(*) FROM materiales WHERE activo=1 AND cantidad>0")),
        ("Materiales agotados", db.scalar("SELECT COUNT(*) FROM materiales WHERE activo=1 AND cantidad<=0")),
        ("Clientes registrados", db.scalar("SELECT COUNT(*) FROM clientes")),
        ("Cotizaciones", db.scalar("SELECT COUNT(*) FROM cotizaciones")),
        ("Remisiones", db.scalar("SELECT COUNT(*) FROM remisiones")),
        ("Facturas", db.scalar("SELECT COUNT(*) FROM facturas")),
        ("Cartera pendiente", db.scalar("SELECT COALESCE(SUM(saldo),0) FROM facturas WHERE estado NOT IN ('anulada','borrador')")),
    ]
    for i, (k, v) in enumerate(resumen, start=4):
        a = portada.cell(row=i, column=2, value=k)
        a.font = Font(name="Montserrat", size=11, bold=True, color="FF292F33")
        b = portada.cell(row=i, column=3, value=v)
        b.font = FUENTE_DATO
        if k == "Cartera pendiente":
            b.number_format = MONEDA_FMT
    portada.column_dimensions["A"].width = 2.8
    portada.column_dimensions["B"].width = 32
    portada.column_dimensions["C"].width = 26

    RUTA_CONTROL.parent.mkdir(parents=True, exist_ok=True)
    wb.save(RUTA_CONTROL)
    return RUTA_CONTROL


# =====================================================================
#  EXPORTAR — archivo RESPALDO (volcado completo)
# =====================================================================
TABLAS_RESPALDO = ["config", "usuarios", "clientes", "categorias", "productos", "inventario",
                   "materiales", "movimientos_material", "listas", "movimientos_inventario",
                   "pedidos", "pedido_items", "cotizaciones", "cotizacion_items",
                   "remisiones", "remision_items", "facturas", "factura_items", "pagos",
                   "consecutivos", "mensajes", "bitacora"]


def exportar_respaldo() -> Path:
    wb = Workbook()
    wb.remove(wb.active)
    info = wb.create_sheet("_RESPALDO")
    info["A1"] = "RESPALDO COMPLETO — IMATEC S.A.S."
    info["A1"].font = FUENTE_TITULO
    info["A3"] = f"Generado: {datetime.now().strftime('%d/%m/%Y %I:%M %p')}"
    info["A4"] = "Una hoja por cada tabla de la base de datos. No modifique este archivo a mano."
    info.column_dimensions["A"].width = 90

    for tabla in TABLAS_RESPALDO:
        try:
            filas = db.q(f"SELECT * FROM {tabla}")
        except Exception:
            continue
        ws = wb.create_sheet(tabla[:31])
        cols = ([c["name"] for c in db.q(f"PRAGMA table_info({tabla})")])
        if not cols:
            continue
        for i, h in enumerate(cols, start=1):
            c = ws.cell(row=1, column=i, value=h)
            c.font, c.fill, c.alignment = FUENTE_CAB, FILL_CAB, CENTRO
        for r, fila in enumerate(filas, start=2):
            for i, h in enumerate(cols, start=1):
                v = fila.get(h)
                if h == "password_hash":
                    v = "(protegido)"
                ws.cell(row=r, column=i, value=v)
        for i, h in enumerate(cols, start=1):
            ws.column_dimensions[get_column_letter(i)].width = min(max(len(h) + 4, 12), 40)
        ws.freeze_panes = "A2"

    RUTA_RESPALDO.parent.mkdir(parents=True, exist_ok=True)
    wb.save(RUTA_RESPALDO)
    return RUTA_RESPALDO


def exportar_todo() -> dict:
    return {"control": str(exportar_control()), "respaldo": str(exportar_respaldo())}
