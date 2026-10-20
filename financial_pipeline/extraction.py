from pathlib import Path

from .discovery import ReportSource


def extract_record(company: dict, pdf: Path, source: ReportSource, year: int) -> dict:
    """TODO: extract statement pages locally using deterministic PDF parsing.

    Preserve reported values and per-metric units, currency, source labels, and
    1-based PDF pages. Require review of year, consolidation, and auditor evidence.
    Unknown or ambiguous values remain None and need manual input. No prediction,
    estimation, model extraction, or filling from the supplied expected results.
    Net income must identify the exact reported line and attribution basis and
    explain its derivation. A reconciliation requires cited source components;
    never invent a reconciliation from revenue and total assets.
    """
    raise NotImplementedError("Statement extraction is not implemented yet.")
