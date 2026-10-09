"""Number formatting shared by charts and slide copy. Half-up rounding, so 0.625 shows as 63%."""
from decimal import ROUND_HALF_UP, Decimal


def num(x: float, d: int = 0) -> str:
    q = Decimal(1).scaleb(-d)
    return f"{Decimal(str(x)).quantize(q, rounding=ROUND_HALF_UP):,}"


def pct(x: float, d: int = 0) -> str:
    return num(x * 100, d) + "%"
