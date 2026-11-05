"""Prices, discounts and GST. All money is in rupees, rounded to the paisa."""
GST_RATES = {"standard": 0.18, "reduced": 0.05, "zero": 0.0}


def with_gst(net: float, rate: str = "standard") -> float:
    if rate not in GST_RATES:
        raise ValueError(f"unknown GST rate {rate!r}")
    return round(net * (1 + GST_RATES[rate]), 2)


def discount(amount: float, percent: float) -> float:
    if not 0 <= percent <= 100:
        raise ValueError("percent must be between 0 and 100")
    return round(amount * (1 - percent / 100), 2)
