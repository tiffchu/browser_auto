import argparse
import csv
import json
from pathlib import Path

from .discovery import find_latest_audited_report
from .download import obtain_pdf
from .extraction import extract_record
from .spreadsheet import write_workbook


def main() -> int:
    parser = argparse.ArgumentParser(description="Audited financial collection scaffold")
    parser.add_argument("--config", type=Path, default=Path("config.json"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    config_path = args.config.resolve()
    root = config_path.parent
    config = json.loads(config_path.read_text(encoding="utf-8"))
    year = config["target_fiscal_year"]
    with (root / config["companies_csv"]).open(encoding="utf-8-sig", newline="") as stream:
        companies = list(csv.DictReader(stream))
    if args.dry_run:
        print(f"DRY RUN: {len(companies)} companies; fiscal year {year}")
        for company in companies:
            print(f"  {company['company_id']}: {company['company_name']}")
        print(f"Planned workbook: {root / config['output_xlsx']}")
        print("Discovery, download, and extraction remain implementation placeholders.")
        return 0

    from jsonschema import Draft202012Validator, FormatChecker

    schema_path = Path(__file__).resolve().parent.parent / "schemas/financial_record.schema.json"
    validator = Draft202012Validator(
        json.loads(schema_path.read_text(encoding="utf-8")), format_checker=FormatChecker()
    )
    records, outcomes = [], []
    for company in companies:
        try:
            source = find_latest_audited_report(company, year)
            pdf = obtain_pdf(source, company["company_id"], root)
            record = extract_record(company, pdf, source, year)
            validator.validate(record)
            if record["fiscal_year"] != year or record["company_id"] != company["company_id"]:
                raise ValueError("Extracted company or fiscal year does not match the request.")
            if record["status"] == "ready":
                records.append(record)
            outcomes.append({"company_id": company["company_id"], "status": record["status"]})
        except Exception as error:
            outcomes.append({"company_id": company["company_id"], "status": "error",
                             "error": f"{type(error).__name__}: {error}"})
    report = root / config["run_report"]
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(outcomes, indent=2), encoding="utf-8")
    if records:
        write_workbook(records, root / config["output_xlsx"])
    print(f"Ready: {len(records)}/{len(companies)}; run report: {report}")
    return 0 if companies and len(records) == len(companies) else 1


if __name__ == "__main__":
    raise SystemExit(main())
