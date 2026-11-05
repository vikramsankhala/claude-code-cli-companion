"""A shopping cart. Lines are (sku, unit_price, quantity, gst_rate)."""
from dataclasses import dataclass, field

from .pricing import discount, with_gst


@dataclass
class Cart:
    lines: list[tuple[str, float, int, str]] = field(default_factory=list)

    def add(self, sku: str, unit_price: float, qty: int = 1, rate: str = "standard") -> None:
        if qty <= 0:
            raise ValueError("quantity must be positive")
        self.lines.append((sku, unit_price, qty, rate))

    def net(self) -> float:
        return round(sum(p * q for _, p, q, _ in self.lines), 2)

    def total(self, coupon_percent: float = 0) -> float:
        gross = sum(with_gst(p * q, r) for _, p, q, r in self.lines)
        return discount(gross, coupon_percent)
