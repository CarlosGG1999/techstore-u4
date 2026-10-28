"""Ejecuta los escenarios E01-E15 de datos/escenarios.csv contra el dominio.

Uso:
    python escenarios.py          -> tabla resumen con los 15 casos
    python escenarios.py E07      -> detalle de un solo caso (para captura)
"""
import sys
from decimal import Decimal

from cargar_csv import load_fixture, rows
from app.domain import DomainException, Money, OrderItem
from app.specifications import discount_rate

PRECIOS = {x["sku"]: Decimal(x["precio_mxn"]) for x in rows("productos.csv")}


def descuento(order):
    return f"{int(discount_rate(order) * 100)}%"


# Cada escenario: lista de pasos (nombre, funcion(order)). Si un paso lanza
# una excepcion de dominio, el escenario termina en rechazo.
PASOS = {
    "E01": [("evaluar descuento", descuento)],
    "E02": [("evaluar descuento", descuento)],
    "E03": [("confirm()", lambda o: o.confirm())],
    "E04": [("evaluar descuento", descuento)],
    "E05": [("evaluar descuento", descuento)],
    "E06": [("confirm()", lambda o: o.confirm())],
    "E07": [("confirm()", lambda o: o.confirm())],
    "E08": [("add_item(SKU003 x2)",
             lambda o: o.add_item(OrderItem("SKU003", 2, Money(PRECIOS["SKU003"]))))],
    "E09": [("evaluar descuento", descuento)],
    "E10": [("evaluar descuento", descuento)],
    "E11": [("confirm()", lambda o: o.confirm()),
            ("ship('')", lambda o: o.ship(""))],
    "E12": [("confirm()", lambda o: o.confirm()),
            ("confirm() otra vez", lambda o: o.confirm())],
    "E13": [("confirm()", lambda o: o.confirm()),
            ("ship('GUIA-001')", lambda o: o.ship("GUIA-001")),
            ("cancel('motivo')", lambda o: o.cancel("Cliente lo solicito"))],
    "E14": [("confirm()", lambda o: o.confirm()),
            ("ship('GUIA-001')", lambda o: o.ship("GUIA-001")),
            ("return_order()", lambda o: o.return_order())],
    "E15": [("confirm()", lambda o: o.confirm()),
            ("ship('GUIA-001')", lambda o: o.ship("GUIA-001")),
            ("deliver()", lambda o: o.deliver())],
}


def correr(caso):
    order = load_fixture()[caso["pedido_id"]]  # pedido limpio para cada caso
    inicial = order.status.value
    log, resultado, rechazado = [], "", False
    for nombre, paso in PASOS[caso["caso_id"]]:
        try:
            valor = paso(order)
            log.append(f"{nombre}: ok")
            if valor is not None:           # evaluacion de descuento
                resultado = valor
        except DomainException as exc:
            log.append(f"{nombre}: RECHAZADO ({type(exc).__name__}: {exc})")
            resultado, rechazado = f"rechazo ({type(exc).__name__})", True
            break
    if not resultado:
        resultado = "exito"
    esperado = caso["objetivo"]
    if esperado.endswith("%"):
        coincide = resultado == esperado
    elif esperado.startswith("rechazo"):
        coincide = rechazado
    else:
        coincide = resultado == "exito"
    eventos = [e.name for e in order.events]
    return inicial, log, resultado, order.status.value, eventos, esperado, coincide


def main():
    casos = rows("escenarios.csv")
    if len(sys.argv) > 1:
        casos = [c for c in casos if c["caso_id"] == sys.argv[1].upper()]
        if not casos:
            sys.exit("Caso no encontrado. Usa E01 ... E15")
        c = casos[0]
        ini, log, res, fin, ev, esp, ok = correr(c)
        print(f"Caso:            {c['caso_id']}  (pedido {c['pedido_id']})")
        print(f"Accion:          {c['accion']}")
        print(f"Estado inicial:  {ini}")
        for linea in log:
            print(f"  - {linea}")
        print(f"Resultado real:  {res}   (esperado: {esp})")
        print(f"Estado final:    {fin}")
        print(f"Eventos:         {ev if ev else 'sin evento'}")
        print(f"Coincide:        {'SI' if ok else 'NO'}")
        return

    print(f"{'Caso':<5} {'Pedido':<6} {'Inicial':<7} {'Resultado real':<34} {'Final':<10} {'Eventos'}")
    print("-" * 110)
    for c in casos:
        ini, log, res, fin, ev, esp, ok = correr(c)
        evs = ", ".join(ev) if ev else "sin evento"
        print(f"{c['caso_id']:<5} {c['pedido_id']:<6} {ini:<7} {res:<34} {fin:<10} {evs}")
    print("-" * 110)


if __name__ == "__main__":
    main()
