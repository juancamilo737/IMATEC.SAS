"""Estado de cuenta del cliente: cartera, vencimientos y cupo de crédito."""
from datetime import date

from . import db


def _dias_vencido(fecha_vencimiento: str):
    """Días transcurridos desde el vencimiento. Negativo si aún no vence.

    Devuelve None cuando la factura no tiene fecha —las que la relación de
    cartera marca «PDTE PAGO»—. Antes devolvía 0, y un cero se lee como «vence
    hoy»: esas facturas se colaban en la franja corriente como si estuvieran
    al día. No se sabe su antigüedad, y decirlo es mejor que suponerla.
    """
    from .utils import parse_fecha
    v = parse_fecha(fecha_vencimiento)
    return (date.today() - v).days if v else None


def cartera(cliente_id: int) -> dict:
    """Radiografía de la deuda del cliente, agrupada por antigüedad.

    Las franjas (corriente, 1-30, 31-60, 61-90, +90) son las que usa
    cualquier área de cobranza para saber qué tan grave es un atraso. Se
    agrega una más, «sin fecha», para las facturas que la relación de cartera
    trae marcadas «PDTE PAGO»: se deben, pero nadie les pactó plazo, así que
    no se pueden clasificar por antigüedad ni dar por corrientes.
    """
    facturas = db.q("""SELECT id, numero, fecha_emision, fecha_vencimiento, total, saldo, estado
                       FROM facturas
                       WHERE cliente_id=? AND saldo > 0
                         AND estado NOT IN ('anulada','borrador','pagada')
                       ORDER BY fecha_vencimiento""", (cliente_id,))

    franjas = {"corriente": 0.0, "d1_30": 0.0, "d31_60": 0.0, "d61_90": 0.0,
               "d90": 0.0, "sin_fecha": 0.0}
    vencido = por_vencer = sin_fecha = 0.0
    vencidas = []

    for f in facturas:
        saldo = float(f["saldo"] or 0)
        dias = _dias_vencido(f["fecha_vencimiento"])
        f["dias_vencido"] = dias
        if dias is None:
            franjas["sin_fecha"] += saldo
            sin_fecha += saldo
        elif dias <= 0:
            franjas["corriente"] += saldo
            por_vencer += saldo
        else:
            vencido += saldo
            vencidas.append(f)
            if dias <= 30:
                franjas["d1_30"] += saldo
            elif dias <= 60:
                franjas["d31_60"] += saldo
            elif dias <= 90:
                franjas["d61_90"] += saldo
            else:
                franjas["d90"] += saldo

    total = vencido + por_vencer + sin_fecha
    cli = db.q1("SELECT cupo_credito, condicion_pago FROM clientes WHERE id=?", (cliente_id,)) or {}
    cupo = float(cli.get("cupo_credito") or 0)

    return {
        "total": round(total, 2),
        "vencido": round(vencido, 2),
        "por_vencer": round(por_vencer, 2),
        "sin_fecha": round(sin_fecha, 2),
        "franjas": {k: round(v, 2) for k, v in franjas.items()},
        "facturas": facturas,
        "vencidas": vencidas,
        "n_vencidas": len(vencidas),
        "cupo": cupo,
        "cupo_disponible": round(max(cupo - total, 0), 2),
        "cupo_usado_pct": round(min(total / cupo * 100, 100), 1) if cupo > 0 else 0,
        "plazo": int(cli.get("condicion_pago") or 0),
        # Una factura «PDTE PAGO» no se puede probar vencida, pero tampoco
        # deja al cliente al día: se debe y sin plazo acordado.
        "al_dia": vencido <= 0.01 and sin_fecha <= 0.01,
    }


def resumen_actividad(cliente_id: int) -> dict:
    """Lo que el cliente tiene en curso y lo que requiere que él actúe."""
    return {
        # cotizaciones esperando que el cliente apruebe o rechace
        "por_aprobar": db.q("""SELECT *, date(fecha,'+'||validez_dias||' day') AS vence
                               FROM cotizaciones
                               WHERE cliente_id=? AND estado='enviada'
                               ORDER BY fecha DESC""", (cliente_id,)),
        "en_camino": db.q("""SELECT * FROM remisiones
                             WHERE cliente_id=? AND estado IN ('pendiente','despachada')
                             ORDER BY fecha DESC""", (cliente_id,)),
        "solicitudes_abiertas": db.scalar(
            "SELECT COUNT(*) FROM pedidos WHERE cliente_id=? AND estado IN ('nuevo','en_cotizacion')",
            (cliente_id,)),
        "comprado_anio": db.scalar("""SELECT COALESCE(SUM(total),0) FROM facturas
                                      WHERE cliente_id=? AND estado NOT IN ('anulada','borrador')
                                      AND strftime('%Y',fecha_emision)=strftime('%Y','now','localtime')""",
                                   (cliente_id,)),
        "n_facturas_anio": db.scalar("""SELECT COUNT(*) FROM facturas
                                        WHERE cliente_id=? AND estado NOT IN ('anulada','borrador')
                                        AND strftime('%Y',fecha_emision)=strftime('%Y','now','localtime')""",
                                     (cliente_id,)),
    }
