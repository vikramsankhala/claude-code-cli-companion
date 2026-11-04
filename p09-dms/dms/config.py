"""Enterprise settings. Values here are ILLUSTRATIVE: confirm retention periods with legal counsel."""
REGIONS = {  # data residency: each region keeps its own database and file store
    "in": "India (Mumbai)",
    "eu": "European Union (Frankfurt)",
    "us": "United States (Virginia)",
}
CLASSIFICATION = ["public", "internal", "confidential", "restricted"]  # low -> high
STATUSES = {  # allowed workflow transitions
    "draft": {"review"},
    "review": {"draft", "approved"},
    "approved": {"archived"},
    "archived": set(),
}
RETENTION_YEARS = {  # (region, doc_type) -> years after last update; default 7
    ("in", "invoice"): 8, ("in", "contract"): 8, ("in", "hr-record"): 7,
    ("eu", "invoice"): 10, ("eu", "contract"): 10, ("eu", "hr-record"): 3,
    ("us", "invoice"): 7, ("us", "contract"): 7, ("us", "hr-record"): 7,
}
DEFAULT_RETENTION_YEARS = 7
