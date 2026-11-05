"""Line and order totals with discount and GST, to the paisa."""
from decimal import ROUND_HALF_UP, Decimal

PAISA = Decimal("0.01")


def money(x) -> Decimal:
    return Decimal(str(x)).quantize(PAISA, rounding=ROUND_HALF_UP)


def line_total(unit_price, qty: int, gst_pct: float, discount_pct: float = 0) -> Decimal:
    """Discount applies to the price before tax; GST applies to the discounted amount."""
    if qty < 1:
        raise ValueError("quantity must be at least 1")
    if not 0 <= discount_pct <= 100:
        raise ValueError("discount must be between 0 and 100 per cent")
    net = Decimal(str(unit_price)) * qty * (1 - Decimal(str(discount_pct)) / 100)
    tax = net * Decimal(str(gst_pct)) / 100
    return Decimal(int((net + tax) * 100)) / 100   # planted bug 2: truncates instead of rounding


def order_total(lines) -> Decimal:
    return money(sum((line_total(**ln) for ln in lines), Decimal("0")))
