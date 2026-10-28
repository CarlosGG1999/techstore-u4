# TechStore - Domain-Driven Design (U4 FIME UANL)
# Carlos Hugo Garcia Gomez 226690
# Hernandez Garza Saul ALejandro 2226664
# Alan Bertín Castillo Martínez 2226653

Proyecto desarrollado para la actividad práctica de la Unidad 4 (Componentes de Lógica de Negocio), aplicando arquitectura orientada a dominio (DDD), FastAPI y pruebas automatizadas en Python.

Los datos se leen de archivos CSV y se manejan **en memoria**: no hay base de datos, y los cambios se pierden al cerrar el programa.

## Estructura del Proyecto
- `app/domain.py`: entidades `Order` y `Customer`, Value Objects `Money` y `OrderItem`, máquina de estados, Domain Events y excepciones de dominio.
- `app/specifications.py`: Specification Pattern (AND, OR, NOT), reglas de descuento y `discount_rate()`.
- `app/api.py`: API REST con FastAPI (solo traduce HTTP al dominio; no contiene reglas de negocio).
- `tests/`: pruebas de dominio (`test_domain.py`), de API (`test_api.py`) y `conftest.py` (recarga los pedidos antes de cada prueba).
- `datos/`: CSV de carga inicial (clientes, productos, pedidos, detalle de pedidos y escenarios E01-E15).
- `cargar_csv.py`: convierte los CSV en objetos del dominio.

## Pasos de Instalación y Ejecución

Requiere Python 3.11 o superior.

1. **Crear y activar el entorno virtual:**
   ```bash
   python -m venv .venv
   .venv\Scripts\Activate.ps1      # Windows PowerShell
   # .venv\Scripts\activate.bat    # Windows CMD
   # source .venv/bin/activate     # macOS / Linux
   ```

2. **Instalar dependencias:**
   ```bash
   python -m pip install fastapi uvicorn pytest httpx
   ```

3. **Verificar la carga de datos** (debe mostrar los 16 pedidos en `DRAFT`):
   ```bash
   python cargar_csv.py
   ```

4. **Ejecutar las pruebas:**
   ```bash
   python -m pytest -q
   ```

5. **Iniciar la API:**
   ```bash
   uvicorn app.api:app --reload
   ```
   - Documentación interactiva (Swagger): http://127.0.0.1:8000/docs
   - Contrato OpenAPI: http://127.0.0.1:8000/openapi.json

   Para repetir una prueba desde cero, reinicia el servidor: los pedidos se recargan de los CSV.

## Reglas de Negocio

**Value Objects y entidades**
- `Money` es inmutable, usa `Decimal` y no admite montos negativos ni monedas distintas.
- `OrderItem` exige SKU y cantidad mayor a 0; su subtotal se calcula, no se captura.
- Un pedido admite máximo **20 unidades** (suma de cantidades, no número de renglones), solo en MXN, y solo se le agregan artículos mientras está en `DRAFT`.

**Descuentos** (Specification Pattern)
| Descuento | Condición |
|---|---|
| 10 % | Cliente VIP **Y** total > 500 **Y** al menos 4 unidades **Y** sin promoción activa |
| 5 % | Total > 5000 **Y** sin promoción activa |
| Combinación | Las dos reglas se unen con OR; si ambas se cumplen, gana el 10 % |

**Máquina de estados**
```
DRAFT --confirm--> CONFIRMED --ship--> SHIPPED --deliver--> DELIVERED
                       |                  |
                     cancel             return
                       |                  |
                   CANCELLED           RETURNED
```
| Operación | Requiere | Evento |
|---|---|---|
| `confirm()` | `DRAFT`, al menos un artículo y cliente activo | `OrderConfirmed` |
| `ship(guía)` | `CONFIRMED` y número de guía no vacío | `OrderShipped` |
| `cancel(motivo)` | `CONFIRMED` y motivo no vacío | `OrderCancelled` |
| `deliver()` | `SHIPPED` | `OrderDelivered` |
| `return_order()` | `SHIPPED` | `OrderReturned` |

Siempre se valida primero, se cambia el estado después y el evento se registra al final: una operación inválida no cambia el estado ni agrega eventos.

## Endpoints

| Método | Ruta | Cuerpo | Respuestas |
|---|---|---|---|
| GET | `/orders/{id}` | - | 200, 404 |
| POST | `/orders/{id}/confirm` | - | 200, 404, 409, 422 |
| POST | `/orders/{id}/ship` | `{"tracking_number": "GUIA-123"}` | 200, 404, 409, 422 |
| POST | `/orders/{id}/cancel` | `{"reason": "motivo"}` | 200, 404, 409, 422 |

Traducción de errores de dominio a HTTP:
- **404**: el pedido no existe.
- **409 Conflict**: transición de estado inválida (`InvalidOrderTransition`), por ejemplo confirmar dos veces o cancelar un pedido `SHIPPED`.
- **422**: datos inválidos (`InvalidOrderData`, `OrderItemLimitExceeded`), por ejemplo pedido vacío, cliente inactivo, guía o motivo vacíos.

Ejemplos rápidos (PowerShell):
```powershell
curl.exe -X POST http://127.0.0.1:8000/orders/O001/confirm
curl.exe -X POST http://127.0.0.1:8000/orders/O001/ship -H "Content-Type: application/json" -d '{\"tracking_number\": \"GUIA-123\"}'
```

## Escenarios E01-E15
Los casos de `datos/escenarios.csv` están cubiertos por las pruebas de `tests/test_domain.py` y `tests/test_api.py`: descuentos y valores frontera (E01-E05, E09, E10), pedido vacío y límite de 20 unidades (E06-E08), guía obligatoria y transiciones prohibidas (E11-E13), entrega y devolución (E14-E15).
