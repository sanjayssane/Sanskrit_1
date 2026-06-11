"""Money helpers (TDD §5.5): all storage is integer paise, UI shows rupees."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


def to_paise(rupees: float | int | str | Decimal) -> int:
    """Convert a rupee amount to integer paise, rounding half-up."""
    quantized = Decimal(str(rupees)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return int(quantized * 100)


def to_rupees(paise: int) -> float:
    return paise / 100.0


def fmt_inr(paise: int) -> str:
    sign = "-" if paise < 0 else ""
    return f"{sign}\u20b9{abs(paise) / 100:,.2f}"
