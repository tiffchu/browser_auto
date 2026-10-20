# Agreed extraction and output requirements

This is a skeleton specification, not a completed financial collection run.

- Companies are public companies. The 25 identities in the supplied CSV are now the starter list.
- Target fiscal year end is any date from January 1 through December 31, 2025. Publication may be in 2026.
- Use the **original audited annual consolidated statements** for that fiscal year. Do not substitute later restatements or a later report's comparative column.
- No prediction, financial modelling, estimates, or model extraction. Arithmetic unit conversion and documented reconciliation of actual source figures are permitted.
- Unknown or uncertain values are null in JSON and **Needs manual input** in Excel, with a reason. No automatic zero substitution. Retain a company even if every metric is unresolved.
- Preserve confirmed values when a different metric is unresolved.
- Output monetary values in thousands, as in the example. Preserve the original reported amount, multiplier, currency, exact source label, and pages in the evidence sheet. Do not infer currency from `$`, company location, exchange, or an undefined footnote. No FX conversion.
- A ready status requires verified fiscal year end, original report version, auditor evidence, PDF identity, original publication date, and per-metric evidence. These are factual review assertions; flags alone do not establish correctness.

## Reference example

`inputs/reference/output_example.csv` is an unchanged copy of the supplied CSV. It has 25 company rows (ranks 76-100), contact/business metadata, and paired 2025/2024 figures. The first line of each monetary cell is 2025 and the second is 2024. Parentheses indicate negative printed amounts; trailing footnote markers are retained separately.

`inputs/reference/expected_results.json` preserves the user-supplied expected amounts and all original columns for later regression comparison. Expected amounts never populate an extracted record. Unexplained footnotes remain unresolved. Orion's name marker `(1)` is preserved in the original columns and removed from its matching name; no explanation for the marker is assumed.

The active collection remains 2025 only. The 2024 comparison values, growth percentages, business descriptions, executives, founding year and employee counts are preserved as reference data. They are not new extraction tasks. The initial export uses separate numeric 2025 financial columns, rather than stacking multiple years as text in one cell. Rank is labelled as reference rank, not recalculated.

## Net income explanation

For each company, extraction/review must:

1. Cite the exact line label and PDF page used for the signed net income or loss amount.
2. Identify whether the amount is the consolidated total or attributable to owners. If the intended basis cannot be established, leave net income unresolved. The example alone does not settle this definition across all issuers.
3. Explain whether the value was copied from a reported line or reconciled using audited components. A reconciliation must list the actual components, amounts, signs, and source pages, and agree to the reported result at the source precision. Ambiguity or a failed reconciliation needs manual input.
4. State source units and any conversion to thousands. Keep losses negative.

The CSV gives expected net income values but contains no audited statement breakdowns. Company-specific derivations will be written after the original statements are obtained, not reverse engineered from the expected answers. `net_income_derivation` is required for a ready net income metric; it is not a forecast or generic explanation.

## Implementation remaining

Issuer report discovery, downloads, PDF extraction, evidence verification, company-specific derivations, and expected-versus-extracted comparison are still explicit TODOs. Current validation checks structural completeness and policy gates. It cannot independently establish that a cited statement supports an amount.
