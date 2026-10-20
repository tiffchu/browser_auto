from dataclasses import dataclass


@dataclass(frozen=True)
class ReportSource:
    url: str | None
    local_pdf: str | None
    publication_date: str | None
    # The discovery implementation must establish both, using source evidence.
    audited: bool
    original_verified: bool
    fiscal_year_end: str | None


def find_original_audited_report(company: dict, target_year: int) -> ReportSource:
    """Find original audited annual statements for a year ending in target_year.

    TODO: issuer-specific discovery, access policy checks, original publication
    verification, fiscal year end, auditor evidence, and supplied file checks.
    Exclude later restatements and later annual-report comparative columns.
    Preserve former company names/tickers when matching the original issuer.
    """
    raise NotImplementedError("Company report discovery is not configured yet.")
