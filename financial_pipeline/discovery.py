from dataclasses import dataclass


@dataclass(frozen=True)
class ReportSource:
    url: str | None
    local_pdf: str | None
    publication_date: str | None
    # The discovery implementation must establish both, using source evidence.
    audited: bool
    latest_verified: bool


def find_latest_audited_report(company: dict, target_year: int) -> ReportSource:
    """Find and verify a report containing the requested fiscal-year figures.

    TODO: issuer-specific discovery, access policy checks, date comparison,
    auditor opinion evidence, and supplied URL/local file verification.
    """
    raise NotImplementedError("Company report discovery is not configured yet.")
