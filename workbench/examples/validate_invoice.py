"""Chapter 39 example: validate_invoice.py. Run: python validate_invoice.py"""
from pydantic import BaseModel


class Invoice(BaseModel):
    number: str
    amount_inr: float
inv = Invoice.model_validate_json('{"number":"S-102","amount_inr":"45000"}')
print(inv.amount_inr + 1)   # 45001.0, string coerced
