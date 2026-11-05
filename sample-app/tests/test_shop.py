import pytest

from shop.api import order_summary
from shop.cart import Cart
from shop.pricing import discount, with_gst


def test_gst_rates():
    assert with_gst(100) == 118.0
    assert with_gst(100, "reduced") == 105.0
    with pytest.raises(ValueError):
        with_gst(100, "luxury")


def test_discount_bounds():
    assert discount(200, 10) == 180.0
    with pytest.raises(ValueError):
        discount(200, 120)


def test_cart_total_and_summary():
    c = Cart()
    c.add("TEA-250G", 180.0, 2, "reduced")
    c.add("MUG", 350.0, 1)
    assert c.net() == 710.0
    assert c.total() == 791.0
    assert order_summary(c, 10)["total"] == 711.9
