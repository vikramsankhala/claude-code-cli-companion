"""An order 'API' stub: builds the JSON a real endpoint would return."""
import json

from .cart import Cart


def order_summary(cart: Cart, coupon_percent: float = 0) -> dict:
    return {"lines": len(cart.lines), "net": cart.net(), "total": cart.total(coupon_percent),
            "currency": "INR"}


if __name__ == "__main__":
    c = Cart()
    c.add("TEA-250G", 180.0, 2, "reduced")
    c.add("MUG", 350.0, 1)
    print(json.dumps(order_summary(c, 10), indent=2))
