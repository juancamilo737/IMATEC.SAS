"""
Facturación electrónica DIAN (Colombia).

IMPORTANTE — léase antes de usar en producción:
Una factura electrónica sólo tiene validez legal cuando se transmite a la DIAN firmada
digitalmente con el certificado de la empresa y bajo una resolución de numeración vigente.
Ese paso lo debe hacer la DIAN habilitando a IMATEC S.A.S. o un Proveedor Tecnológico
autorizado (Factus, Alegra, Siigo, Facture, etc.).

Lo que este módulo SÍ hace hoy:
  · Construye el documento con todos los campos exigidos por el Anexo Técnico 1.9.
  · Calcula el CUFE con el algoritmo oficial (SHA-384) — verificable.
  · Genera el contenido del código QR y el XML UBL 2.1.
Lo que NO hace (requiere habilitación DIAN + certificado digital):
  · Firmar el XML y transmitirlo a la DIAN.
El envío queda aislado en `enviar_a_dian()`, listo para conectar el proveedor
que la empresa contrate, sin tocar el resto del sistema.
"""
import hashlib
from datetime import datetime
from xml.sax.saxutils import escape

from . import db

TIPOS_DOC = {"NIT": "31", "CC": "13", "CE": "22", "PAS": "41"}


def calcular_cufe(factura: dict, empresa: dict, items: list) -> str:
    """CUFE según Anexo Técnico DIAN 1.9 (SHA-384 sobre la cadena oficial)."""
    def n(v):
        return f"{float(v or 0):.2f}"

    base_iva = sum(float(i["cantidad"]) * float(i["precio"]) *
                   (1 - float(i.get("descuento_pct") or 0) / 100)
                   for i in items if float(i.get("iva_pct") or 0) > 0)
    hora = factura.get("hora_emision") or "00:00:00-05:00"

    cadena = "".join([
        str(factura["numero"]),                        # NumFac
        str(factura["fecha_emision"]),                 # FecFac
        hora,                                          # HorFac
        n(factura["subtotal"]),                        # ValFac
        "01", n(factura["iva"]),                       # CodImp1 (IVA) + ValImp1
        "04", n(0),                                    # INC
        "03", n(0),                                    # ICA
        n(factura["total"]),                           # ValTot
        str(empresa.get("nit", "")),                   # NitFE
        str(factura["cliente_documento"]),             # NumAdq
        str(empresa.get("dian_clave_tecnica", "")),    # ClTec
        "2" if empresa.get("dian_ambiente") == "produccion" else "1",  # TipoAmbiente
    ])
    return hashlib.sha384(cadena.encode("utf-8")).hexdigest()


def datos_qr(factura: dict, empresa: dict) -> str:
    """Contenido del código QR impreso en la representación gráfica."""
    return (
        f"NumFac: {factura['numero']}\n"
        f"FecFac: {factura['fecha_emision']}\n"
        f"NitFac: {empresa.get('nit','')}\n"
        f"DocAdq: {factura['cliente_documento']}\n"
        f"ValFac: {float(factura['subtotal'] or 0):.2f}\n"
        f"ValIva: {float(factura['iva'] or 0):.2f}\n"
        f"ValTolFac: {float(factura['total'] or 0):.2f}\n"
        f"CUFE: {factura.get('cufe','')}"
    )


def generar_xml_ubl(factura: dict, empresa: dict, cliente: dict, items: list) -> str:
    """XML UBL 2.1 sin firmar. La firma la aplica el proveedor tecnológico."""
    def e(v):
        return escape(str(v if v is not None else ""))

    lineas = []
    for i, it in enumerate(items, start=1):
        base = float(it["cantidad"]) * float(it["precio"]) * \
               (1 - float(it.get("descuento_pct") or 0) / 100)
        iva = base * float(it.get("iva_pct") or 0) / 100
        lineas.append(f"""    <cac:InvoiceLine>
      <cbc:ID>{i}</cbc:ID>
      <cbc:InvoicedQuantity unitCode="{e(it.get('unidad','UND'))}">{float(it['cantidad']):.2f}</cbc:InvoicedQuantity>
      <cbc:LineExtensionAmount currencyID="COP">{base:.2f}</cbc:LineExtensionAmount>
      <cac:TaxTotal>
        <cbc:TaxAmount currencyID="COP">{iva:.2f}</cbc:TaxAmount>
        <cac:TaxSubtotal>
          <cbc:TaxableAmount currencyID="COP">{base:.2f}</cbc:TaxableAmount>
          <cbc:TaxAmount currencyID="COP">{iva:.2f}</cbc:TaxAmount>
          <cac:TaxCategory>
            <cbc:Percent>{float(it.get('iva_pct') or 0):.2f}</cbc:Percent>
            <cac:TaxScheme><cbc:ID>01</cbc:ID><cbc:Name>IVA</cbc:Name></cac:TaxScheme>
          </cac:TaxCategory>
        </cac:TaxSubtotal>
      </cac:TaxTotal>
      <cac:Item><cbc:Description>{e(it['descripcion'])}</cbc:Description></cac:Item>
      <cac:Price><cbc:PriceAmount currencyID="COP">{float(it['precio']):.2f}</cbc:PriceAmount></cac:Price>
    </cac:InvoiceLine>""")

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
         xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
         xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cbc:UBLVersionID>UBL 2.1</cbc:UBLVersionID>
  <cbc:CustomizationID>10</cbc:CustomizationID>
  <cbc:ProfileID>DIAN 2.1: Factura Electrónica de Venta</cbc:ProfileID>
  <cbc:ID>{e(factura['numero'])}</cbc:ID>
  <cbc:UUID schemeName="CUFE-SHA384">{e(factura.get('cufe',''))}</cbc:UUID>
  <cbc:IssueDate>{e(factura['fecha_emision'])}</cbc:IssueDate>
  <cbc:IssueTime>{e(factura.get('hora_emision','00:00:00-05:00'))}</cbc:IssueTime>
  <cbc:InvoiceTypeCode>01</cbc:InvoiceTypeCode>
  <cbc:DocumentCurrencyCode>COP</cbc:DocumentCurrencyCode>
  <cac:AccountingSupplierParty>
    <cac:Party>
      <cac:PartyName><cbc:Name>{e(empresa.get('razon_social'))}</cbc:Name></cac:PartyName>
      <cac:PartyTaxScheme>
        <cbc:RegistrationName>{e(empresa.get('razon_social'))}</cbc:RegistrationName>
        <cbc:CompanyID schemeID="{e(empresa.get('dv',''))}" schemeName="31">{e(empresa.get('nit'))}</cbc:CompanyID>
      </cac:PartyTaxScheme>
      <cac:PhysicalLocation><cac:Address>
        <cbc:CityName>{e(empresa.get('ciudad'))}</cbc:CityName>
        <cac:AddressLine><cbc:Line>{e(empresa.get('direccion'))}</cbc:Line></cac:AddressLine>
      </cac:Address></cac:PhysicalLocation>
    </cac:Party>
  </cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty>
    <cac:Party>
      <cac:PartyName><cbc:Name>{e(cliente['razon_social'])}</cbc:Name></cac:PartyName>
      <cac:PartyTaxScheme>
        <cbc:RegistrationName>{e(cliente['razon_social'])}</cbc:RegistrationName>
        <cbc:CompanyID schemeID="{e(cliente.get('dv',''))}" schemeName="{TIPOS_DOC.get(cliente.get('tipo_documento','NIT'),'31')}">{e(cliente['documento'])}</cbc:CompanyID>
      </cac:PartyTaxScheme>
      <cac:PhysicalLocation><cac:Address>
        <cbc:CityName>{e(cliente.get('ciudad'))}</cbc:CityName>
        <cac:AddressLine><cbc:Line>{e(cliente.get('direccion'))}</cbc:Line></cac:AddressLine>
      </cac:Address></cac:PhysicalLocation>
    </cac:Party>
  </cac:AccountingCustomerParty>
  <cac:TaxTotal>
    <cbc:TaxAmount currencyID="COP">{float(factura['iva'] or 0):.2f}</cbc:TaxAmount>
  </cac:TaxTotal>
  <cac:LegalMonetaryTotal>
    <cbc:LineExtensionAmount currencyID="COP">{float(factura['subtotal'] or 0):.2f}</cbc:LineExtensionAmount>
    <cbc:TaxExclusiveAmount currencyID="COP">{float(factura['subtotal'] or 0):.2f}</cbc:TaxExclusiveAmount>
    <cbc:PayableAmount currencyID="COP">{float(factura['total'] or 0):.2f}</cbc:PayableAmount>
  </cac:LegalMonetaryTotal>
{chr(10).join(lineas)}
</Invoice>"""


def preparar(factura_id: int) -> dict:
    """Calcula CUFE, QR y XML de una factura y los guarda."""
    from .documentos import factura_completa
    f = factura_completa(factura_id)
    emp = db.empresa()
    f["hora_emision"] = datetime.now().strftime("%H:%M:%S-05:00")
    f["cliente_documento"] = f["cliente"]["documento"]
    cufe = calcular_cufe(f, emp, f["items"])
    f["cufe"] = cufe
    qr = datos_qr(f, emp)
    xml = generar_xml_ubl(f, emp, f["cliente"], f["items"])
    resolucion = emp.get("dian_resolucion", "")
    db.ex("UPDATE facturas SET cufe=?, qr_data=?, resolucion_dian=? WHERE id=?",
          (cufe, qr, resolucion, factura_id))
    return {"cufe": cufe, "qr": qr, "xml": xml}


def habilitada() -> bool:
    """¿La empresa ya tiene los datos DIAN cargados?"""
    emp = db.empresa()
    return bool(emp.get("nit") and emp.get("dian_resolucion") and emp.get("dian_clave_tecnica"))


def enviar_a_dian(factura_id: int) -> dict:
    """Punto único de integración con el Proveedor Tecnológico.
    Cuando IMATEC contrate uno, aquí se implementa la llamada a su API."""
    if not habilitada():
        return {"ok": False, "estado": "sin_habilitar",
                "mensaje": "Faltan los datos DIAN (NIT, resolución de numeración y clave "
                           "técnica). Cárguelos en Configuración. Mientras tanto la factura "
                           "se guarda y se imprime, pero no se transmite a la DIAN."}
    return {"ok": False, "estado": "sin_proveedor",
            "mensaje": "Datos DIAN cargados. Falta conectar el Proveedor Tecnológico "
                       "en app/dian.py -> enviar_a_dian()."}
