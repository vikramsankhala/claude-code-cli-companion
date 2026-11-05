"""A few sample orders for demo D8's MCP tool."""
ORDERS = {
    "ORD-1001": {"customer": "Asha Traders", "status": "dispatched", "lines": [["TEA-250", 4], ["MUG-01", 2]],
                 "courier": "BlueDart", "eta": "2026-11-08"},
    "ORD-1002": {"customer": "Kaveri Stores", "status": "packed", "lines": [["KTL-02", 1]],
                 "courier": None, "eta": "2026-11-10"},
    "ORD-1003": {"customer": "Nilgiri Cafe", "status": "on hold: GSTIN mismatch", "lines": [["HNY-500", 6]],
                 "courier": None, "eta": None},
}
