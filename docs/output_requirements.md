# Agreed extraction and output requirements

The general collector remains a skeleton. The reviewed 25-company 2025 test is complete; its records and workbook are separate from the original example benchmarks.

- Companies are public companies. The 25 identities in the supplied CSV are now the starter list.
- Collect exactly one fiscal year: **YEAR-1**, where YEAR is the computer's local calendar year when the run starts. Runs in 2026 target fiscal year ends from January 1 through December 31, 2025. Runs in 2027 target fiscal year ends in 2026. Publication can be in the following year. Do not fall back to an older year when the requested statements are unavailable.
- Use the **original audited annual consolidated statements** for that fiscal year. Do not substitute later restatements or a later report's comparative column.
- Use **reported consolidated net income/loss**. Exclude total comprehensive income, other comprehensive income, adjusted profit measures, and attributable-to-owners subtotals. If the reported net income line cannot be identified with certainty, mark it for manual input.
- No prediction, financial modelling, estimates, or model extraction. Arithmetic unit conversion is permitted. Any explanation using audited components must support the reported net income line, never replace it with a reconstructed amount.
- Unknown or uncertain values are null in JSON and **Needs manual input** in Excel, with a reason. No automatic zero substitution. Retain a company even if every metric is unresolved.
- Preserve confirmed values when a different metric is unresolved.
- Output full monetary values in CAD, overriding the example's `(000s)` headings. Expand source thousands/millions. Convert USD using the last published Bank of Canada FXUSDCAD rate on/before December 31 of YEAR-1; 2025 uses December 31, 2025, at 1.3706 CAD per USD. Apply this requested calendar year-end convention to revenue, net income and assets for all fiscal ends. Indicate whether values were converted from USD. Rank descending CAD revenue. Preserve original amounts, units, currency, labels and source locations. Do not infer currency from `$` or company location. Unsupported currency or missing FX requires manual input.
- A ready status requires verified fiscal year end, original report version, auditor evidence, source identity, publication or auditor report date, and per-metric evidence. Auditor report dates are explicitly labelled and never assumed to be publication dates. PDF pages are 1-based; HTML may use specific printed-page/section locators. These are factual review assertions; flags alone do not establish correctness.

## Reference example

`inputs/reference/output_example.csv` is an unchanged copy of the supplied CSV. It has 25 company rows (ranks 76-100), contact/business metadata, and paired 2025/2024 figures. The first line of each monetary cell is 2025 and the second is 2024. Parentheses indicate negative printed amounts; trailing footnote markers are retained separately.

`inputs/reference/expected_results.json` preserves the user-supplied expected amounts and all original columns for later regression comparison. Expected amounts never populate an extracted record. Unexplained footnotes remain unresolved. Orion's name marker `(1)` is preserved in the original columns and removed from its matching name; no explanation for the marker is assumed.

The active collection contains YEAR-1 only, with no prior-year comparison or growth percentage. Supplied historical values remain reference data and are not automatically reused as extraction output. Rank is recalculated from confirmed CAD revenue; missing revenues remain unranked at the end. The reviewed test is frozen to 2025 and must not be relabelled as 2026 next year.

## Net income explanation

For each company, extraction/review must:

1. Copy and cite the exact reported annual net income/loss line label and PDF page for YEAR-1. A statement titled "comprehensive income" may contain the required net income line; the selected line must still be net income/loss, not a comprehensive income/loss total.
2. Use the reported consolidated total before attribution to owners/non-controlling interests. Capture `net_income_measure` as `reported_net_income` and `net_income_basis` as `consolidated_total`. An uncertain classification requires manual input.
3. Explain the reported amount and source. If audited components are included to explain how that reported amount arises, cite those components and pages. The output value must remain the reported net income/loss figure. Do not reconstruct a substitute amount or use comprehensive income. Ambiguity requires manual input.
4. State source units, expansion to full dollars, and USD-to-CAD conversion where applicable. Keep losses negative. Expanded figures retain the original source's rounding precision.

The CSV gives expected net income values but contains no audited statement breakdowns. Company-specific derivations will be written after the original statements are obtained, not reverse engineered from the expected answers. `net_income_derivation` is required for a ready net income metric; it is not a forecast or generic explanation.

## Implementation remaining

General issuer report discovery, automatic PDF extraction and automatic evidence verification remain TODOs. Explicit test-report downloads and reviewed company-specific explanations are implemented. Current validation checks structural completeness and policy gates; it cannot independently establish that a cited statement supports an amount. One test source (Canaccord) uses an explicitly identified reproduction of the original company-authored report because direct issuer PDF access was blocked.
