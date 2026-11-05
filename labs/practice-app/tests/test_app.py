"""These pass: they cover the parts without planted bugs. The bugs are in ../exercises."""
import json
import threading
import urllib.request

import pytest

from shopkeeper import catalogue, pricing
from shopkeeper.inventory import Inventory, OutOfStock
from shopkeeper.server import serve


def test_find_and_unknown_sku():
    assert catalogue.find("MUG-01")["price"] == 249.00
    with pytest.raises(KeyError):
        catalogue.find("NOPE")


def test_line_total_rejects_bad_input():
    with pytest.raises(ValueError):
        pricing.line_total(100, 0, 18)
    with pytest.raises(ValueError):
        pricing.line_total(100, 1, 18, discount_pct=120)


def test_whole_rupee_totals():
    assert pricing.line_total(100, 2, 18) == pricing.money("236.00")


def test_reserve_and_release():
    inv = Inventory({"TEA-250": 10})
    inv.reserve("TEA-250", 3)
    assert inv.available("TEA-250") == 7
    inv.release("TEA-250", 3)
    assert inv.available("TEA-250") == 10
    with pytest.raises(OutOfStock):
        inv.reserve("TEA-250", 50)


def test_server_item_lookup():
    srv = serve(0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{srv.server_address[1]}/items/KTL-02"
        with urllib.request.urlopen(url, timeout=5) as r:
            assert json.load(r)["name"] == "Electric kettle"
        with urllib.request.urlopen(url.replace("items/KTL-02", "orders/ord-1002"), timeout=5) as r:
            assert json.load(r)["status"] == "packed"
    finally:
        srv.shutdown()
