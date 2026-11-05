"""Chapter 43, weeks 3 and 4: the EMI calculator as it stands after the exercises.

Day 12 writes emi(); day 18 finds the zero-rate bug; day 17 adds the amortisation schedule.
Try the exercises yourself first, then compare with this file."""


def emi(principal: float, annual_rate_pct: float, years: int) -> float:
    """Equated monthly instalment for a loan."""
    n = years * 12
    if n <= 0:
        raise ValueError("years must be positive")
    r = annual_rate_pct / 12 / 100
    if r == 0:                      # day 18: the formula divides by zero at 0%
        return principal / n
    return principal * r * (1 + r) ** n / ((1 + r) ** n - 1)


def amortisation_schedule(principal: float, annual_rate_pct: float, years: int) -> list[dict]:
    """Month-by-month split of each instalment into interest and principal (day 17).
    Every amount is rounded to the paisa as it is posted, so the rows add up exactly."""
    r = annual_rate_pct / 12 / 100
    payment = round(emi(principal, annual_rate_pct, years), 2)
    balance, rows, n = round(principal, 2), [], years * 12
    for month in range(1, n + 1):
        interest = round(balance * r, 2)
        repaid = balance if month == n else round(payment - interest, 2)   # last month closes the loan
        balance = round(balance - repaid, 2)
        rows.append({"month": month, "interest": interest, "principal": repaid, "balance": balance})
    return rows


if __name__ == "__main__":
    print(f"EMI: ₹{emi(1_000_000, 9, 20):,.2f}")
    for rate in (8, 9, 10):         # day 15: the rate table, merged from its branch
        print(rate, round(emi(1_000_000, rate, 20), 2))
