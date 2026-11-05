"""Stock levels and reservations."""


class OutOfStock(Exception):
    pass


class Inventory:
    def __init__(self, stock: dict[str, int]):
        self.stock = dict(stock)
        self.reserved: dict[str, int] = {}

    def available(self, sku: str) -> int:
        return self.stock.get(sku, 0) - self.reserved.get(sku, 0)

    def reserve(self, sku: str, qty: int) -> None:
        if qty < 1:
            raise ValueError("quantity must be at least 1")
        if qty >= self.available(sku):                 # planted bug 3: cannot reserve the last unit
            raise OutOfStock(f"{sku}: asked {qty}, {self.available(sku)} available")
        self.reserved[sku] = self.reserved.get(sku, 0) + qty

    def release(self, sku: str, qty: int) -> None:
        self.reserved[sku] = max(0, self.reserved.get(sku, 0) - qty)
