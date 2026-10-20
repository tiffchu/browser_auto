# Audited financial statement collection

Collect revenue, reported net income/loss, and total assets for fiscal years ending in YEAR-1, using original audited statements. YEAR is the computer's local calendar year at run time: a 2026 run targets 2025, and a 2027 run targets 2026. Collect exactly that one year. The general discovery/extraction pipeline remains a scaffold. A separate reviewed test for the latest 25-company input is complete.

## Completed 2025 test

`outputs/financials_2025_test.xlsx` contains 25 companies ranked by descending CAD revenue, with full-dollar revenue, reported consolidated net income/loss and assets. Sixteen USD reporters use Bank of Canada FXUSDCAD **1.3706**, dated **2025-12-31**, for all three metrics. Nine CAD reporters are unchanged. The same calendar year-end rate applies to non-calendar fiscal years. Source rounding is retained; expanding millions or thousands does not create additional precision.

The `Source data` tab retains original amounts, units, currency, conversion formulas, auditor dates, reported labels, source locations, net income explanations and URLs. Canaccord's original company-authored report was reviewed through an HTML reproduction because the issuer PDF was blocked; both URLs are retained. Lululemon uses its original SEC HTML filing. No PDF page numbers are invented for HTML sources. All 75 amounts are confirmed; no estimates populate the test.

Rebuild this frozen test after dependencies and source inputs are present:

```powershell
.\.venv\Scripts\python.exe scripts/prepare_test_run.py
node scripts/build_test_workbook.mjs
```

The Node builder requires `@oai/artifact-tool`, supplied by the desktop workspace runtime. It recalculates and checks every amount/rank, tests FX changes and saves rendered previews under `tmp/workbook_previews/`. `outputs/test_run_2025_records.json` preserves the validated source records and `outputs/test_run_2025_checks.json` records the output checks. `inputs/test_run_2025.csv` is the unchanged latest input; `inputs/test_run_2025_reviewed.json` holds reviewed transcriptions. `scripts/acquire_test_reports.py` downloads the explicit report manifest and Bank of Canada response; it does not discover reports. The reviewed test does not automatically collect next year's statements or use last year's data as a substitute.

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
5. **Export:** retain every company, including unresolved rows. Expand source units to full dollars, convert USD to CAD at the verified calendar year-end Bank of Canada rate, indicate conversion, and rank by CAD revenue. Preserve original amounts, currency, units and source locations. USD amounts without a verified rate require manual input. Export only YEAR-1; older values and nonfinancial columns remain reference data only. The general Python writer remains a fallback; the reviewed test uses the Artifact Tool builder.

The schema allows null values for unresolved fields. Each metric has a status and reason. Only confirmed values with complete evidence become numeric output cells. Unknowns display `Needs manual input`. Structural validation and policy gates are implemented; factual source verification remains part of extraction/review.

## Net income requirement

Copy the reported consolidated annual net income/loss line and record its source. The explanation describes that reported amount. A comprehensive income/loss candidate or an uncertain match needs manual input. Supporting audited components can explain the reported result but cannot replace it. No prior-year comparison or growth column is required.

## Verification

```powershell
.\.venv\Scripts\python.exe -m compileall -q financial_pipeline
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m financial_pipeline --dry-run
```

The 22 tests verify reference import, YEAR-1 rollover, source/year gates, exclusion of comprehensive income, manual-input handling, HTML locators, signs, units, CAD conversion, year-end rate selection and revenue ordering. The separate reviewed test has source verification, company-specific explanations and rendered workbook checks. General automatic report discovery and extraction remain unimplemented.
