from decimal import Decimal

class Specification:
    def is_satisfied_by(self, order) -> bool:
        raise NotImplementedError
        
    def __and__(self, other):
        return AndSpec(self, other)
        
    def __or__(self, other):
        return OrSpec(self, other)
        
    def __invert__(self):
        return NotSpec(self)

class AndSpec(Specification):
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def is_satisfied_by(self, order) -> bool:
        return self.left.is_satisfied_by(order) and self.right.is_satisfied_by(order)

class OrSpec(Specification):
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def is_satisfied_by(self, order) -> bool:
        return self.left.is_satisfied_by(order) or self.right.is_satisfied_by(order)

class NotSpec(Specification):
    def __init__(self, spec):
        self.spec = spec
    def is_satisfied_by(self, order) -> bool:
        return not self.spec.is_satisfied_by(order)

# --- Especificaciones Concretas para TechStore ---

class MinimumAmountSpec(Specification):
    def __init__(self, min_amount: Decimal):
        self.min_amount = min_amount
    def is_satisfied_by(self, order) -> bool:
        return order.total.amount > self.min_amount

class VIPCustomerSpec(Specification):
    def is_satisfied_by(self, order) -> bool:
        return order.customer.is_vip

class MinimumUnitsSpec(Specification):
    def __init__(self, min_units: int):
        self.min_units = min_units
    def is_satisfied_by(self, order) -> bool:
        return order.units >= self.min_units

class ActivePromotionSpec(Specification):
    def is_satisfied_by(self, order) -> bool:
        return order.has_promotion


# --- Reglas de descuento de TechStore (composicion AND / OR / NOT) ---

# 10 %: VIP, total > 500, al menos 4 unidades y SIN promocion activa.
TEN_PERCENT_RULE = (
    MinimumAmountSpec(Decimal("500"))
    & VIPCustomerSpec()
    & MinimumUnitsSpec(4)
    & ~ActivePromotionSpec()
)

# 5 %: total > 5000 y SIN promocion activa.
FIVE_PERCENT_RULE = MinimumAmountSpec(Decimal("5000")) & ~ActivePromotionSpec()

# Elegible para algun descuento: cualquiera de las dos reglas (OR).
ANY_DISCOUNT_RULE = TEN_PERCENT_RULE | FIVE_PERCENT_RULE


def discount_rate(order) -> Decimal:
    """Devuelve 0.10, 0.05 o 0. Si se cumplen ambas reglas, gana la de 10 %."""
    if not ANY_DISCOUNT_RULE.is_satisfied_by(order):
        return Decimal("0")
    if TEN_PERCENT_RULE.is_satisfied_by(order):
        return Decimal("0.10")
    return Decimal("0.05")
