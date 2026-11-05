"""The product catalogue. Prices are in rupees; GST rates are illustrative."""
ITEMS = [
    {"sku": "TEA-250", "name": "Assam tea, 250 g", "price": 180.00, "gst": 5},
    {"sku": "MUG-01", "name": "Steel mug", "price": 249.00, "gst": 12},
    {"sku": "KTL-02", "name": "Electric kettle", "price": 1499.00, "gst": 18},
    {"sku": "BSC-12", "name": "Biscuits, pack of 12", "price": 60.00, "gst": 18},
    {"sku": "HNY-500", "name": "Forest honey, 500 g", "price": 425.00, "gst": 5},
    {"sku": "FLT-03", "name": "Tea strainer", "price": 99.00, "gst": 12},
    {"sku": "JAR-04", "name": "Glass storage jar", "price": 210.00, "gst": 18},
]


def find(sku: str) -> dict:
    for item in ITEMS:
        if item["sku"] == sku:
            return item
    raise KeyError(f"unknown SKU {sku!r}")


def page(items: list, number: int, size: int = 3) -> list:
    """Return page `number` of `items`. Pages are numbered from 1, as the API documents."""
    if number < 1 or size < 1:
        raise ValueError("page number and size start at 1")
    start = number * size                       # planted bug 1: pages are 1-based
    return items[start:start + size]
