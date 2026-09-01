"""Carga al inventario los productos extraídos del histórico de cotizaciones.

De dónde sale cada precio, y por qué:

El «LISTADO DE PRECIOS» trae una columna COSTO. Comparándola contra lo que
IMATEC cotizó de verdad, los precios facturados quedan ~33% por encima
(mediana 1,33x sobre 87 productos coincidentes; sólo 1 de 87 iguales). Es
decir, esa columna es el costo, no el precio de venta: publicarla habría
hecho que vendieran sin margen.

Por eso el precio de venta sale del **último valor cotizado** a un cliente
real, que es el dato más confiable que existe, y el COSTO se guarda aparte
como costo_unitario para poder ver el margen.

Se publican los productos cotizados dos veces o más: son los recurrentes y
están validados por el uso. Los que aparecen una sola vez quedan cargados
pero sin publicar, porque suelen ser fabricaciones puntuales o erratas.
"""
import json
import re
import unicodedata
from pathlib import Path

from . import db
from .importar_precios import CATEGORIAS, MATERIALES, _clasificar, _sku

VECES_PARA_PUBLICAR = 2

UNIDADES = {
    "METRO LINEAL": "Metros", "METRO": "Metros", "MTS": "Metros",
    "TUBO X 6 MTS": "Tubos de 6 m", "ACCESORIO": "Unidades", "UNIDAD": "Unidades",
    "UND": "Unidades", "FABRICACION": "Unidades", "ROLLO": "Rollos",
    "1/4 GALON": "Galones", "GALON": "Galones", "LAMINA": "Láminas", "KILO": "Kilos",
}


def _unidad(u: str) -> str:
    u = " ".join(str(u or "").upper().split())
    return UNIDADES.get(u, u.title() if u else "Unidades")


def _diametro(desc: str) -> str:
    """Saca la medida de la descripción: TUBERIA A/C SCH 40 2 " -> 2\"."""
    m = re.findall(r'(\d+(?:\s+\d+/\d+)?(?:/\d+)?)\s*"', desc)
    return (m[-1].strip() + '"') if m else ""


def importar_items(ruta_json, usuario: str = "histórico de cotizaciones") -> dict:
    items = json.loads(Path(ruta_json).read_text(encoding="utf-8"))
    usados = {r["sku"] for r in db.q("SELECT sku FROM materiales")}
    # el costo, cuando el listado de precios ya lo cargó
    costos = {" ".join(r["descripcion"].upper().split()): r["costo_unitario"]
              for r in db.q("SELECT descripcion, costo_unitario FROM materiales "
                            "WHERE costo_unitario > 0")}

    res = {"nuevos": 0, "actualizados": 0, "publicados": 0, "omitidos": 0}

    for it in items:
        desc = " ".join(str(it["descripcion"]).split())
        precio = float(it.get("precio_ultimo") or 0)
        if len(desc) < 5 or precio <= 0:
            res["omitidos"] += 1
            continue

        publicar = 1 if it.get("veces", 0) >= VECES_PARA_PUBLICAR else 0
        costo = costos.get(desc.upper(), 0)
        nota = (f"Cotizado {it['veces']} vez/veces"
                + (f", última el {it['ultima_fecha']}" if it.get("ultima_fecha") else ""))

        existente = db.q1("SELECT id, publicado FROM materiales WHERE descripcion=?", (desc,))
        if existente:
            db.ex("""UPDATE materiales SET precio_venta=?, unidad=?, notas=?,
                     publicado=MAX(publicado, ?),
                     actualizado_en=datetime('now','localtime') WHERE id=?""",
                  (round(precio), _unidad(it.get("unidad")), nota, publicar, existente["id"]))
            res["actualizados"] += 1
        else:
            db.ex("""INSERT INTO materiales
                     (sku,categoria,material,diametro,descripcion,cantidad,unidad,
                      costo_unitario,precio_venta,publicado,notas)
                     VALUES(?,?,?,?,?,0,?,?,?,?,?)""",
                  (_sku(desc, _diametro(desc), usados),
                   _clasificar(desc, CATEGORIAS) or "Otros",
                   _clasificar(desc, MATERIALES),
                   _diametro(desc), desc, _unidad(it.get("unidad")),
                   round(costo), round(precio), publicar, nota))
            res["nuevos"] += 1
        if publicar:
            res["publicados"] += 1

    res["costos_a_revisar"] = _marcar_costos_dudosos()
    db.log(usuario, "importar_items", "materiales", str(ruta_json), str(res))
    return res


def _marcar_costos_dudosos() -> int:
    """El listado de precios repite la misma descripción para medidas distintas
    («SOPORTE TIPO PERA» aparece siete veces con siete valores), así que al
    cruzar por descripción algunos quedaron con el costo de otra medida.

    El costo NO se borra: los precios se negocian y ese valor es una referencia
    que la empresa quiere conservar y corregir a mano. Sólo se deja anotado
    para que salte a la vista en el inventario.
    """
    dudosos = db.q("""SELECT id, notas FROM materiales
                      WHERE costo_unitario > 0 AND precio_venta > 0
                        AND (precio_venta < costo_unitario
                             OR precio_venta > costo_unitario * 3.0)""")
    for d in dudosos:
        nota = (d["notas"] or "").replace(" · revisar costo", "")
        db.ex("UPDATE materiales SET notas=? WHERE id=?",
              (f"{nota} · revisar costo".strip(" ·"), d["id"]))
    return len(dudosos)
