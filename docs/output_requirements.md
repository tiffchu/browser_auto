# Agreed extraction and output requirements

This is a skeleton specification, not a completed financial collection run.

- Companies are public companies. The 25 identities in the supplied CSV are now the starter list.
- Collect exactly one fiscal year: **YEAR-1**, where YEAR is the computer's local calendar year when the run starts. Runs in 2026 target fiscal year ends from January 1 through December 31, 2025. Runs in 2027 target fiscal year ends in 2026. Publication can be in the following year. Do not fall back to an older year when the requested statements are unavailable.
- Use the **original audited annual consolidated statements** for that fiscal year. Do not substitute later restatements or a later report's comparative column.
- Use **reported consolidated net income/loss**. Exclude total comprehensive income, other comprehensive income, adjusted profit measures, and attributable-to-owners subtotals. If the reported net income line cannot be identified with certainty, mark it for manual input.
- No prediction, financial modelling, estimates, or model extraction. Arithmetic unit conversion is permitted. Any explanation using audited components must support the reported net income line, never replace it with a reconstructed amount.
- Unknown or uncertain values are null in JSON and **Needs manual input** in Excel, with a reason. No automatic zero substitution. Retain a company even if every metric is unresolved.
- Preserve confirmed values when a different metric is unresolved.
- Output monetary values in thousands, as in the example. Preserve the original reported amount, multiplier, currency, exact source label, and pages in the evidence sheet. Do not infer currency from `$`, company location, exchange, or an undefined footnote. No FX conversion.
- A ready status requires verified fiscal year end, original report version, auditor evidence, PDF identity, original publication date, and per-metric evidence. These are factual review assertions; flags alone do not establish correctness.

## Reference example

`inputs/reference/output_example.csv` is an unchanged copy of the supplied CSV. It has 25 company rows (ranks 76-100), contact/business metadata, and paired 2025/2024 figures. The first line of each monetary cell is 2025 and the second is 2024. Parentheses indicate negative printed amounts; trailing footnote markers are retained separately.

`inputs/reference/expected_results.json` preserves the user-supplied expected amounts and all original columns for later regression comparison. Expected amounts never populate an extracted record. Unexplained footnotes remain unresolved. Orion's name marker `(1)` is preserved in the original columns and removed from its matching name; no explanation for the marker is assumed.

The active collection contains YEAR-1 only, with no prior-year comparison or growth percentage. The supplied 2025/2024 values and nonfinancial metadata remain reference data and are not automatically rolled forward or reused as extraction output. Filenames, worksheet title and numeric financial column headings use the resolved target year. Rank is labelled as reference rank, not recalculated.

## Net income explanation

For each company, extraction/review must:

1. Copy and cite the exact reported annual net income/loss line label and PDF page for YEAR-1. A statement titled "comprehensive income" may contain the required net income line; the selected line must still be net income/loss, not a comprehensive income/loss total.
2. Use the reported consolidated total before attribution to owners/non-controlling interests. Capture `net_income_measure` as `reported_net_income` and `net_income_basis` as `consolidated_total`. An uncertain classification requires manual input.
3. Explain the reported amount and source. If audited components are included to explain how that reported amount arises, cite those components and pages. The output value must remain the reported net income/loss figure. Do not reconstruct a substitute amount or use comprehensive income. Ambiguity requires manual input.
4. State source units and any conversion to thousands. Keep losses negative.

The CSV gives expected net income values but contains no audited statement breakdowns. Company-specific derivations will be written after the original statements are obtained, not reverse engineered from the expected answers. `net_income_derivation` is required for a ready net income metric; it is not a forecast or generic explanation.

## Implementation remaining

Issuer report discovery, downloads, PDF extraction, evidence verification, company-specific derivations, and expected-versus-extracted comparison are still explicit TODOs. Current validation checks structural completeness and policy gates. It cannot independently establish that a cited statement supports an amount.
