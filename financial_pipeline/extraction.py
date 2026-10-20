from pathlib import Path

from .discovery import ReportSource


def extract_record(company: dict, pdf: Path, source: ReportSource, year: int) -> dict:
    """TODO: extract statement pages locally using deterministic PDF parsing.

    Preserve reported values and per-metric units, currency, source labels, and
    1-based PDF pages. Require review of year, consolidation, and auditor evidence.
    Unknown or ambiguous values remain None and need manual input. No prediction,
    estimation, model extraction, or filling from the supplied expected results.
    Copy the reported consolidated net income/loss line for the requested year.
    Never substitute total comprehensive income, other comprehensive income,
    adjusted profit, or an attributable-to-owners subtotal. Record the measure
    as reported_net_income and cite the exact line, units, and page. The derivation
    explains that reported amount; it must not reconstruct a substitute amount.
    Use only the requested YEAR-1 column, with no older-year fallback.
    """
    raise NotImplementedError("Statement extraction is not implemented yet.")
