from datetime import date


def previous_fiscal_year(run_date: date | None = None) -> int:
    """Target fiscal years ending in the prior calendar year, using local run date.

    Missing original audited statements for that year require manual input;
    do not silently fall back to a different fiscal year.
    """
    return (run_date or date.today()).year - 1
