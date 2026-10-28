# TechStore — Unidad 4: Componentes de Lógica de Negocio

Proyecto académico desarrollado para FIME–UANL. Implementa un núcleo de pedidos en Python con enfoque Domain-Driven Design (DDD), Specification Pattern, Domain Events y una API FastAPI.

## Integrantes

- **Carlos Hugo García Gómez** — Matrícula **2226690**
- **Hernández Garza Saúl Alejandro** — Matrícula **2226664**
- **Alan Bertín Castillo Martínez** — Matrícula **2226653**

> Los datos proceden de CSV y permanecen en memoria. No hay base de datos ni descuento de inventario; al reiniciar la aplicación se restablecen los pedidos.

## Requisitos
Python 3.11 o superior.

## Instalación

```bash
python -m venv .venv
# PowerShell: .venv\Scripts\Activate.ps1
# Windows CMD: .venv\Scripts\activate.bat
# macOS/Linux: source .venv/bin/activate
python -m pip install fastapi uvicorn pytest httpx
```

## Ejecución

```bash
python cargar_csv.py      # Carga 16 pedidos en DRAFT
python escenarios.py      # Ejecuta E01–E15
python -m pytest -q     # Ejecuta pruebas de dominio y API
uvicorn app.api:app --reload
```

Swagger: http://127.0.0.1:8000/docs · OpenAPI: http://127.0.0.1:8000/openapi.json

## Estructura

- `app/domain.py`: entidades `Order`, `Customer`; objetos de valor `Money`, `OrderItem`; estados, invariantes, excepciones y eventos.
- `app/specifications.py`: especificaciones componibles con AND (`&`), OR (`|`) y NOT (`~`) y cálculo `discount_rate()`.
- `app/api.py`: controlador HTTP sin duplicación de reglas de negocio.
- `datos/`: `clientes.csv`, `productos.csv`, `pedidos.csv`, `detalle_pedidos.csv`, `escenarios.csv`.
- `cargar_csv.py`: carga y relaciona los CSV.
- `escenarios.py`: ejecuta los 15 escenarios.
- `tests/`: pruebas de dominio, API y fixtures.

## Reglas de negocio

- Los importes se expresan con `Decimal` en MXN. `Money` es inmutable y no acepta montos negativos.
- `OrderItem` requiere SKU y cantidad positiva. El subtotal se calcula automáticamente.
- Un pedido admite **hasta 20 unidades en total** (sumando cantidades), solo se agregan artículos estando en `DRAFT`, y solo se confirma si tiene artículos y cliente activo.
- Descuento **10 %**: VIP **AND** total **> 500** **AND** unidades **>= 4** **AND NOT** promoción activa.
- Descuento **5 %**: total **> 5000** **AND NOT** promoción activa.
- Las reglas se combinan con OR y, si coinciden, prevalece el 10 %.
- Estados permitidos: `DRAFT → CONFIRMED → SHIPPED → DELIVERED`; `CONFIRMED → CANCELLED`; `SHIPPED → RETURNED`.
- Se generan `OrderConfirmed`, `OrderShipped`, `OrderCancelled`, `OrderDelivered` y `OrderReturned` solo tras una transición exitosa.

## API REST

| Método | Ruta | Cuerpo | Códigos principales |
|---|---|---|---|
| GET | `/orders/{id}` | — | 200, 404 |
| POST | `/orders/{id}/confirm` | — | 200, 404, 409, 422 |
| POST | `/orders/{id}/ship` | `{"tracking_number":"GUIA-001"}` | 200, 404, 409, 422 |
| POST | `/orders/{id}/cancel` | `{"reason":"Solicitud del cliente"}` | 200, 404, 409, 422 |

HTTP 404 = pedido inexistente; 409 = transición inválida; 422 = datos inválidos. Las operaciones se realizan en memoria y las pruebas deben partir de fixtures limpios.

## Verificación / trazabilidad

| Escenarios | Requisito principal |
|---|---|
| E01–E05 | descuentos, VIP y promoción activa |
| E06–E10 | pedido vacío, máximo de unidades y umbrales |
| E11–E13 | envío sin guía y transiciones prohibidas |
| E14–E15 | devolución y entrega exitosas |

Ejemplo de fronteras adicionales: **500 exactos no supera 500** y **5000 exactos no supera 5000**. La prueba adicional `tests/test_frontera_5000.py` puede incorporarse para comprobar explícitamente el segundo límite.
