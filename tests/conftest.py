import pytest

from cargar_csv import load_fixture


@pytest.fixture(autouse=True)
def pedidos_limpios():
    """Recarga los pedidos de la API antes de cada prueba (estado independiente)."""
    try:
        from app import api
    except ImportError:  # por si se ejecutan solo pruebas de dominio
        yield
        return
    api.orders.clear()
    api.orders.update(load_fixture())
    yield
