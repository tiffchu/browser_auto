from pathlib import Path

from .discovery import ReportSource


def obtain_pdf(source: ReportSource, company_id: str, root: Path) -> Path:
    """TODO: resolve local PDFs or download verified candidates to data/pdfs.

    Implement access checks, timeouts/retries, PDF content validation, safe
    filenames, and source metadata persistence before enabling downloads.
    """
    raise NotImplementedError("PDF acquisition is not implemented yet.")
