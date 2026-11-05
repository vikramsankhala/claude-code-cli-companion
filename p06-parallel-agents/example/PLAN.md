# Plan: bulk discounts and an order receipt

## Goal
Shops can give automatic discounts on large orders, and customers get a plain-text receipt.

## Tasks

### Task: bulk-discount
- Files: shop/pricing.py, tests/test_bulk.py
- Do: add `bulk_discount(net)` giving 5 percent off above ₹5,000 and 10 percent above ₹20,000
- Done when: tests cover both thresholds and the boundaries

### Task: receipt
- Files: shop/receipt.py, tests/test_receipt.py
- Do: add `receipt(cart)` returning a text receipt with one line per item, net, GST and total
- Done when: a test compares the receipt for the sample cart with an expected string

## Risks
- Rounding differences between receipt and cart totals: the receipt must reuse `Cart.total()`.
- Discount and coupon stacking is undefined: out of scope, noted for a later ticket.

## Done when
- [ ] All tasks merged, full test suite green
- [ ] P3 hooks passed on every change, P5 reviewer reports low or medium risk
- [ ] Pull request opened with this plan linked
