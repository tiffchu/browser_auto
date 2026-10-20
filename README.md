# Audited financial statement collection (skeleton)

Collect revenue, reported net income/loss, and total assets for fiscal years ending in YEAR-1, using original audited statements. YEAR is the computer's local calendar year at run time: a 2026 run targets 2025, and a 2027 run targets 2026. Collect exactly that one year. This is a scaffold: discovery, downloads, and extraction still require implementation. The 25 companies and user-supplied expected results are imported from the example CSV; no amounts have been independently collected or verified.

## Setup

Use Python 3.11 or newer. In PowerShell, from this folder:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m financial_pipeline --dry-run
```

The dry run reads configuration and lists intended work. It makes no network requests, creates no workbook, and needs no API key. Running without `--dry-run` currently produces unresolved rows and a run report because discovery is a placeholder. Its exit code is 1 when any company needs manual input.

## Files

- `inputs/companies.csv`: the 25 company identities from the example, with empty IR/PDF/local file fields to complete later.
- `inputs/reference/output_example.csv`: unchanged copy of the supplied CSV.
- `inputs/reference/expected_results.json`: supplied 2025/2024 expected values, separate from extracted data.
- `config.json`: YEAR-1 policy, reported net income requirement, input path, and output filename patterns using `{year}` for the resolved target fiscal year.
- `financial_pipeline/policy.py`: resolves YEAR-1 automatically at run time.
- `docs/output_requirements.md`: agreed source policy, output mapping, and net income explanation requirements.
- `financial_pipeline/discovery.py`: original audited report selection hook.
- `financial_pipeline/download.py`: PDF acquisition hook.
- `financial_pipeline/extraction.py`: deterministic local PDF parsing hook, with no modelling or estimation.
- `financial_pipeline/validation.py`: nulls uncertain values, retains manual-input rows, and enforces fiscal year/source requirements.
- `schemas/financial_record.schema.json`: strict contract for extracted values and evidence.
- `financial_pipeline/spreadsheet.py`: Excel export for confirmed values and explicit manual-input cells; not called by dry run.
- `financial_pipeline/__main__.py`: batch orchestration, with per-company failures kept in a JSON run report.

Put downloaded PDFs in `data/pdfs/` and extraction intermediates in `data/extracted/`. Generated files are ignored by Git. Paths in configuration resolve relative to the config file; company `local_pdf` paths resolve from the same directory.

## Contracts to implement

1. **Discovery:** locate candidates on the issuer website, check applicable access rules, and select the original audited annual consolidated statements for a fiscal year ending in YEAR-1. Record original publication date and auditor evidence. Exclude later restatements and later annual reports' comparative columns. A supplied PDF URL is a candidate, not proof of audited status or original version. If the target year's report is unavailable, require manual input instead of using an older year.
2. **Download:** retrieve a PDF or use a supplied local file. Add timeouts, retries, content checks, and stable filenames. Do not bypass access controls.
3. **Extraction:** use pdfplumber/PyMuPDF to locate relevant statements. Deterministic extraction and OCR support remain TODOs. No prediction, modelling, estimates, or model extraction. Validate records against the schema; the schema alone does not verify financial facts.
4. **Review:** confirm fiscal year end, consolidated scope, original version, auditor evidence, currency, units, and pages. Use reported consolidated net income/loss and explain its exact reported line. Exclude total comprehensive income, other comprehensive income, adjusted measures, and attributable-to-owners subtotals. Do not replace the reported amount with a reconstructed calculation. An uncertain metric is null with a manual-input reason; never replace it with zero or the expected answer.
5. **Export:** retain every company, including unresolved rows. Monetary values are in thousands with per-metric currency, matching the example's units. Preserve reported values, multipliers, and PDF/printed pages in Evidence. The writer creates a new workbook and refuses to overwrite an existing file. Export only YEAR-1; filenames, worksheet title, and financial column headings follow that year automatically. Older values and nonfinancial columns remain reference data only.

The schema allows null values for unresolved fields. Each metric has a status and reason. Only confirmed values with complete evidence become numeric output cells. Unknowns display `Needs manual input`. Structural validation and policy gates are implemented; factual source verification remains part of extraction/review.

## Net income requirement

Copy the reported consolidated annual net income/loss line and record its source. The explanation describes that reported amount. A comprehensive income/loss candidate or an uncertain match needs manual input. Supporting audited components can explain the reported result but cannot replace it. No prior-year comparison or growth column is required.

## Verification

```powershell
.\.venv\Scripts\python.exe -m compileall -q financial_pipeline
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m financial_pipeline --dry-run
```

These verify reference import, YEAR-1 rollover, source/year gates, exclusion of comprehensive income, manual-input handling, signed values, units, schema, and dry-run wiring. No PDF extraction, network request, company-specific derivation, or rendered Excel output has been validated yet.
