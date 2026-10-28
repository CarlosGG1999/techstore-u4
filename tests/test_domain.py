import pytest
from decimal import Decimal

from app.domain import (
    Money, OrderItem, OrderStatus,
    InvalidOrderData, InvalidOrderTransition, OrderItemLimitExceeded,
)
from app.specifications import (
    MinimumAmountSpec, VIPCustomerSpec, ActivePromotionSpec,
    TEN_PERCENT_RULE, FIVE_PERCENT_RULE, discount_rate,
)
from cargar_csv import load_fixture


def pedido(order_id):
    """Pedido nuevo y limpio, cargado desde los CSV."""
    return load_fixture()[order_id]


def confirmar_y_enviar(order):
    order.confirm()
    order.ship("GUIA-001")


# ---------- Value Objects ----------
def test_money_negativo():
    with pytest.raises(InvalidOrderData):
        Money(Decimal("-1"))


def test_money_monedas_distintas():
    with pytest.raises(InvalidOrderData):
        Money(Decimal("10")).add(Money(Decimal("5"), "USD"))


def test_orderitem_cantidad_cero():
    with pytest.raises(InvalidOrderData):
        OrderItem("SKU001", 0, Money(Decimal("10")))


# ---------- Carga de datos ----------
def test_pedido_o001_inicia_draft():
    orders = load_fixture()
    assert orders["O001"].status.value == "DRAFT"
    assert orders["O001"].units == 4
    assert orders["O001"].total.amount == Decimal("2100.00")


def test_se_cargan_16_pedidos_en_draft():
    orders = load_fixture()
    assert len(orders) == 16
    assert all(o.status == OrderStatus.DRAFT for o in orders.values())


# ---------- Reglas del agregado ----------
def test_limite_21_unidades_se_rechaza():
    order = pedido("O009")  # 19 unidades
    with pytest.raises(OrderItemLimitExceeded):
        order.add_item(OrderItem("SKU003", 2, Money(Decimal("100"))))
    assert order.units == 19  # no se modifico el pedido


def test_20_unidades_se_permiten():
    order = pedido("O008")
    assert order.units == 20
    order.confirm()
    assert order.status == OrderStatus.CONFIRMED


def test_cliente_inactivo_no_confirma():
    order = pedido("O003")
    with pytest.raises(InvalidOrderData):
        order.confirm()
    assert order.status == OrderStatus.DRAFT
    assert order.events == []


def test_pedido_vacio_no_confirma():
    order = pedido("O007")
    with pytest.raises(InvalidOrderData):
        order.confirm()
    assert order.status == OrderStatus.DRAFT
    assert order.events == []


# ---------- Specifications y descuentos ----------
def test_descuento_vip_10_por_ciento():
    assert discount_rate(pedido("O001")) == Decimal("0.10")


def test_promocion_activa_bloquea_descuento():
    assert discount_rate(pedido("O005")) == Decimal("0")


def test_descuento_5_por_ciento():
    assert discount_rate(pedido("O006")) == Decimal("0.05")


def test_umbral_500_es_estricto():
    order = pedido("O010")  # total exactamente 500
    assert order.total.amount == Decimal("500")
    assert not MinimumAmountSpec(Decimal("500")).is_satisfied_by(order)
    assert discount_rate(order) == Decimal("0")


def test_minimo_4_unidades_para_10_por_ciento():
    order = pedido("O011")  # 3 unidades
    assert not TEN_PERCENT_RULE.is_satisfied_by(order)
    assert discount_rate(order) == Decimal("0")


def test_cliente_no_vip_sin_descuento():
    assert discount_rate(pedido("O002")) == Decimal("0")


def test_composicion_and_or_not():
    order = pedido("O001")  # VIP, sin promocion
    vip, promo = VIPCustomerSpec(), ActivePromotionSpec()
    assert (vip & ~promo).is_satisfied_by(order)       # AND + NOT
    assert (promo | vip).is_satisfied_by(order)        # OR
    assert not (promo & vip).is_satisfied_by(order)
    assert not FIVE_PERCENT_RULE.is_satisfied_by(order)  # total 2100 < 5000


def test_prioridad_10_sobre_5():
    order = pedido("O001")
    order.add_item(OrderItem("SKU999", 1, Money(Decimal("4000"))))  # total > 5000
    assert FIVE_PERCENT_RULE.is_satisfied_by(order)
    assert TEN_PERCENT_RULE.is_satisfied_by(order)
    assert discount_rate(order) == Decimal("0.10")


# ---------- Maquina de estados y eventos ----------
def test_confirmar_registra_evento():
    order = pedido("O013")
    order.confirm()
    assert order.status == OrderStatus.CONFIRMED
    assert [e.name for e in order.events] == ["OrderConfirmed"]


def test_confirmacion_doble_falla_sin_nuevo_evento():
    order = pedido("O013")
    order.confirm()
    with pytest.raises(InvalidOrderTransition):
        order.confirm()
    assert order.status == OrderStatus.CONFIRMED
    assert len(order.events) == 1


def test_envio_sin_guia_falla_sin_cambiar_estado():
    order = pedido("O012")
    order.confirm()
    with pytest.raises(InvalidOrderData):
        order.ship("   ")
    assert order.status == OrderStatus.CONFIRMED
    assert [e.name for e in order.events] == ["OrderConfirmed"]


def test_no_se_envia_desde_draft():
    order = pedido("O012")
    with pytest.raises(InvalidOrderTransition):
        order.ship("GUIA-001")
    assert order.events == []


def test_cancelar_requiere_motivo():
    order = pedido("O014")
    order.confirm()
    with pytest.raises(InvalidOrderData):
        order.cancel("")
    assert order.status == OrderStatus.CONFIRMED


def test_cancelar_desde_confirmed():
    order = pedido("O014")
    order.confirm()
    order.cancel("Cliente lo solicito")
    assert order.status == OrderStatus.CANCELLED
    assert order.events[-1].name == "OrderCancelled"


def test_cancelar_desde_shipped_falla():
    order = pedido("O014")
    confirmar_y_enviar(order)
    with pytest.raises(InvalidOrderTransition):
        order.cancel("Ya no lo quiero")
    assert order.status == OrderStatus.SHIPPED
    assert [e.name for e in order.events] == ["OrderConfirmed", "OrderShipped"]


def test_entrega_desde_shipped():
    order = pedido("O016")
    confirmar_y_enviar(order)
    order.deliver()
    assert order.status == OrderStatus.DELIVERED
    assert order.events[-1].name == "OrderDelivered"


def test_devolucion_desde_shipped():
    order = pedido("O015")
    confirmar_y_enviar(order)
    order.return_order()
    assert order.status == OrderStatus.RETURNED
    assert order.events[-1].name == "OrderReturned"


def test_no_se_entrega_desde_confirmed():
    order = pedido("O016")
    order.confirm()
    with pytest.raises(InvalidOrderTransition):
        order.deliver()
    assert order.status == OrderStatus.CONFIRMED
