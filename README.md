# Audited financial statement collection (skeleton)

Collect 2025 revenue, net income, and total assets for multiple companies, retaining evidence for every value. This is a scaffold: discovery, downloads, and extraction deliberately require implementation once the companies and reporting rules are known. No financial data is included.

## Setup

Use Python 3.11 or newer. In PowerShell, from this folder:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m financial_pipeline --dry-run
```

The dry run reads configuration and lists the intended work. It makes no network requests, creates no workbook, and needs no API key. Running without `--dry-run` reaches the explicit discovery placeholder.

## Files

- `inputs/companies.csv`: company identifiers and optional IR/PDF URLs or local PDFs. Replace the clearly marked example row.
- `config.json`: target fiscal year, input path, and a new output workbook path.
- `financial_pipeline/discovery.py`: source discovery and latest audited report selection hook.
- `financial_pipeline/download.py`: PDF acquisition hook.
- `financial_pipeline/extraction.py`: local PDF parsing and optional model extraction hook.
- `schemas/financial_record.schema.json`: strict contract for extracted values and evidence.
- `financial_pipeline/spreadsheet.py`: Excel export function for completed records; not called by dry run.
- `financial_pipeline/__main__.py`: batch orchestration, with per-company failures kept in a JSON run report.

Put downloaded PDFs in `data/pdfs/` and extraction intermediates in `data/extracted/`. Generated files are ignored by Git. Paths in configuration resolve relative to the config file; company `local_pdf` paths resolve from the same directory.

## Contracts to implement

1. **Discovery:** locate candidates on the issuer website, check applicable access rules, and select the latest audited annual consolidated report as of the run date. Record report publication date and auditor evidence. A report may contain 2025 comparative figures even when its main fiscal year is later. A supplied PDF URL is a candidate, not proof of audited status or recency.
2. **Download:** retrieve a PDF or use a supplied local file. Add timeouts, retries, content checks, and stable filenames. Do not bypass access controls.
3. **Extraction:** use pdfplumber/PyMuPDF to locate relevant statements. OCR/scanned-document support and any Claude/API integration remain TODOs. Validate optional model responses against the schema; the schema alone does not verify the financial facts.
4. **Review:** confirm the year and column, fiscal year end, consolidated scope, audited status, currency, units, and page evidence. Distinguish total net income from income attributable to shareholders. Never replace a missing number with zero. Flag ambiguity for review.
5. **Export:** one row per company/year; values stay in their reported units, with currency and multiplier beside each metric. Preserve separate PDF page and printed page references for each metric. The writer creates a new workbook and refuses to overwrite an existing file.

The schema allows null values for unresolved fields. Only records explicitly marked `ready` with all required evidence may be exported. Status and evidence must be established by the extraction/review implementation, not inferred from a successful model response. The orchestration validates the structural schema before export.

## Information needed next

- Company list, country/market, and identifiers.
- Whether “2025” means fiscal years ending in 2025 or calendar-year reporting.
- Whether to use the latest restated 2025 comparative figures or the original 2025 filing.
- Net income definition (group total or attributable to owners) and currency/unit preferences.
- Existing spreadsheet/template and column mapping, if any; otherwise use a new workbook.
- Whether model extraction is wanted, and which provider/model to configure.

## Verification

```powershell
.\.venv\Scripts\python.exe -m compileall -q financial_pipeline
.\.venv\Scripts\python.exe -m financial_pipeline --dry-run
```

These verify scaffold wiring only. No real company, PDF extraction, network request, or spreadsheet output has been validated yet.
