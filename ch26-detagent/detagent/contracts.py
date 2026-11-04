"""The one contract the model must meet. Anything else is rejected before it reaches the logic."""
from jsonschema import Draft202012Validator

EXTRACTION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["vendor", "invoice_no", "currency", "amount", "po_number"],
    "properties": {
        "vendor": {"type": "string", "minLength": 2, "maxLength": 120},
        "invoice_no": {"type": "string", "pattern": "^[A-Z0-9-]{3,32}$"},
        "currency": {"enum": ["INR", "EUR", "USD"]},
        "amount": {"type": "number", "exclusiveMinimum": 0, "maximum": 10_000_000},
        "po_number": {"type": ["string", "null"], "pattern": "^PO-[0-9]{4,10}$"},
    },
}
_validator = Draft202012Validator(EXTRACTION_SCHEMA)


def validate(obj) -> list[str]:
    """Return a list of human-readable problems; an empty list means the output is acceptable."""
    return sorted(f"{'/'.join(map(str, e.path)) or '(root)'}: {e.message}" for e in _validator.iter_errors(obj))
