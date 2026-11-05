"""Three tests that FAIL until you fix the planted bugs (demos D1–D3).
Run them on purpose:  python -m pytest exercises -q
The normal test run (python -m pytest) skips this folder."""
from shopkeeper import catalogue, pricing
from shopkeeper.inventory import Inventory


def test_first_page_starts_at_first_item():
    assert [i["sku"] for i in catalogue.page(catalogue.ITEMS, 1)] == ["TEA-250", "MUG-01", "KTL-02"]


def test_totals_round_to_the_nearest_paisa():
    # 3 x 99.00 at 12% GST is 332.64 exactly; 3 x 0.35 at 18% is 1.239, which must round to 1.24
    assert pricing.line_total(99, 3, 12) == pricing.money("332.64")
    assert pricing.line_total(0.35, 3, 18) == pricing.money("1.24")    # 1.239 rounds up; truncation gives 1.23


def test_can_reserve_the_last_unit():
    inv = Inventory({"KTL-02": 1})
    inv.reserve("KTL-02", 1)
    assert inv.available("KTL-02") == 0
