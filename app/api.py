from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from cargar_csv import load_fixture
from app.domain import DomainException, InvalidOrderTransition
from app.specifications import discount_rate

app = FastAPI(title="TechStore U4")
orders = load_fixture()


# --- DTOs de entrada ---
class ShipRequest(BaseModel):
    tracking_number: str


class CancelRequest(BaseModel):
    reason: str


# --- Funciones auxiliares (el controlador NO contiene reglas de negocio) ---
def _get_order(order_id: str):
    order = orders.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="No existe")
    return order


def _execute(action, *args):
    """Ejecuta un metodo del dominio y traduce sus excepciones a HTTP."""
    try:
        action(*args)
    except InvalidOrderTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except DomainException as exc:  # InvalidOrderData, OrderItemLimitExceeded
        raise HTTPException(status_code=422, detail=str(exc))


def _summary(order):
    return {"id": order.id, "status": order.status.value}


# --- Endpoints ---
@app.get("/orders/{order_id}")
def get_order(order_id: str):
    order = _get_order(order_id)
    return {
        "id": order.id,
        "status": order.status.value,
        "customer_id": order.customer.id,
        "units": order.units,
        "total": str(order.total.amount),
        "currency": order.total.currency,
        "discount_percent": int(discount_rate(order) * 100),
        "events": [e.name for e in order.events],
    }


@app.post("/orders/{order_id}/confirm")
def confirm_order(order_id: str):
    order = _get_order(order_id)
    _execute(order.confirm)
    return _summary(order)


@app.post("/orders/{order_id}/ship")
def ship_order(order_id: str, body: ShipRequest):
    order = _get_order(order_id)
    _execute(order.ship, body.tracking_number)
    return _summary(order)


@app.post("/orders/{order_id}/cancel")
def cancel_order(order_id: str, body: CancelRequest):
    order = _get_order(order_id)
    _execute(order.cancel, body.reason)
    return _summary(order)
