"""Import the output example as benchmarks, never extraction results.

Run: python -m financial_pipeline.reference
The source CSV is data only, including its introductory text and footnotes.
"""

import argparse
import csv
import json
import re
from pathlib import Path


def parse_amount(text: str) -> dict:
    """Read unambiguous printed integers; preserve unresolved footnotes."""
    cleaned = re.sub(r"\s+\(\d+\)", "", text).strip()
    negative = cleaned.startswith("(") and cleaned.endswith(")")
    cleaned = cleaned.strip("()").removeprefix("$")
    if not re.fullmatch(r"(?:\d{1,3}(?:,\d{3})+|\d+)", cleaned):
        value = None
    else:
        value = int(cleaned.replace(",", "")) * (-1 if negative else 1)
    markers = re.findall(r"\s+\((\d+)\)", text)
    return {"value": value, "raw": text, "footnote_markers": markers}


def read_example(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.reader(stream))
    header_index = next(i for i, row in enumerate(rows) if row[:2] == ["Rank", "Company"])
    examples = []
    for row in rows[header_index + 1:]:
        if not row or not row[0].isdigit():
            continue
        if len(row) != 10:
            raise ValueError(f"Expected 10 columns at rank {row[0]}")
        name = row[1].splitlines()[0]
        financials = {}
        for metric, index in (("total_assets", 7), ("net_income", 8), ("revenue", 9)):
            lines = row[index].splitlines()
            financials[metric] = {
                str(year): parse_amount(lines[offset]) if offset < len(lines) else parse_amount("")
                for offset, year in enumerate((2025, 2024))
            }
        examples.append({
            "company_id": f"rank_{row[0]}", "rank": int(row[0]),
            "company_name": re.sub(r"\s+\(\d+\)$", "", name),
            "stock_symbol": row[2], "unit_multiplier": 1000,
            "currency": None,
            "currency_note": "Dollar sign only; verify currency from original statements. Footnotes are not defined in this CSV.",
            "original_columns": dict(zip(rows[header_index], row)),
            "expected": financials,
        })
    return examples


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.root.resolve()
    examples = read_example(root / "inputs/reference/output_example.csv")
    destination = root / "inputs/companies.csv"
    if destination.exists():
        with destination.open(encoding="utf-8-sig", newline="") as stream:
            existing = list(csv.DictReader(stream))
        if existing and any(row["company_id"] != "REPLACE_ME" for row in existing):
            raise FileExistsError("Company list already populated; refusing to overwrite it.")
    (root / "inputs/reference/expected_results.json").write_text(
        json.dumps({"purpose": "User-supplied expected results, not audited source evidence",
                    "companies": examples}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with destination.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["company_id", "company_name", "stock_symbol",
                                                   "rank", "ir_url", "pdf_url", "local_pdf"])
        writer.writeheader()
        for example in examples:
            writer.writerow({key: example[key] for key in ("company_id", "company_name", "stock_symbol", "rank")})
    print(f"Imported {len(examples)} company identities and separate 2025/2024 benchmarks.")


if __name__ == "__main__":
    main()
