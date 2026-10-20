from pathlib import Path

from .discovery import ReportSource


def extract_record(company: dict, pdf: Path, source: ReportSource, year: int) -> dict:
    """TODO: extract pages locally, then optionally use a model with the schema.

    Preserve reported values and per-metric units, currency, source labels, and
    1-based PDF pages. Require review of year, consolidation, and auditor evidence.
    Unknown values remain None. Never mark an unresolved record ready.
    """
    raise NotImplementedError("Statement extraction is not implemented yet.")
