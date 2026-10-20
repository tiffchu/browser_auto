"""Exact unit expansion, CAD conversion and revenue ordering; no estimation."""

from decimal import Decimal
from datetime import date


def year_end_usdcad(observations: dict, year: int) -> tuple[str, Decimal]:
    """Last published Bank of Canada observation on/before calendar year end."""
    cutoff = date(year, 12, 31)
    candidates = []
    for row in observations.get("observations", []):
        observed = date.fromisoformat(row["d"])
        value = row.get("FXUSDCAD", {}).get("v")
        if observed.year == year and observed <= cutoff and value:
            rate = Decimal(value)
            if rate.is_finite() and rate > 0:
                candidates.append((row["d"], rate))
    if not candidates:
        raise ValueError(f"No verified Bank of Canada observation for {year}.")
    return max(candidates, key=lambda item: item[0])


def cad_amount(item: dict, usdcad=None) -> Decimal | None:
    if item.get("status") != "ready" or item.get("value") is None:
        return None
    if item.get("unit_multiplier") not in (1, 1000, 1000000, 1000000000):
        return None
    currency = item.get("currency")
    if currency == "CAD":
        rate = Decimal(1)
    elif currency == "USD" and usdcad is not None:
        rate = Decimal(str(usdcad))
    else:
        return None
    amount = Decimal(str(item["value"]))
    if not amount.is_finite() or not rate.is_finite() or rate <= 0:
        return None
    return amount * Decimal(item["unit_multiplier"]) * rate


def rank_by_revenue(records: list[dict], usdcad=None) -> list[dict]:
    """Known revenues descending, unknowns retained last; ties have equal rank."""
    def key(record):
        value = cad_amount(record["revenue"], usdcad)
        return (value is None, -(value or Decimal(0)), record["company_name"].casefold())
    ordered = sorted(records, key=key)
    previous, rank = None, None
    for position, record in enumerate(ordered, 1):
        value = cad_amount(record["revenue"], usdcad)
        if value is None:
            record["revenue_rank"] = None
        else:
            if value != previous:
                rank = position
            record["revenue_rank"] = rank
            previous = value
    return ordered
