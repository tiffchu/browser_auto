import argparse
import csv
import json
from pathlib import Path

from .discovery import find_original_audited_report
from .download import obtain_pdf
from .extraction import extract_record
from .policy import previous_fiscal_year
from .spreadsheet import write_workbook
from .validation import pending_record, prepare_record


def main() -> int:
    parser = argparse.ArgumentParser(description="Audited financial collection scaffold")
    parser.add_argument("--config", type=Path, default=Path("config.json"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    config_path = args.config.resolve()
    root = config_path.parent
    config = json.loads(config_path.read_text(encoding="utf-8"))
    year = previous_fiscal_year()
    policy = {"target_year_rule": "YEAR-1",
              "year_basis": "fiscal_year_end", "report_version": "original",
              "net_income_measure": "reported_net_income", "net_income_basis": "consolidated_total",
              "allow_estimates": False, "allow_model_extraction": False,
              "output_unit_multiplier": 1000, "uncertain_value_label": "Needs manual input"}
    if any(config.get(key) != value for key, value in policy.items()):
        raise ValueError("Policy requires YEAR-1 original statements, reported consolidated net income, no estimates/model extraction, and output in thousands.")
    destination = root / config["output_xlsx"].format(year=year)
    report = root / config["run_report"].format(year=year)
    with (root / config["companies_csv"]).open(encoding="utf-8-sig", newline="") as stream:
        companies = list(csv.DictReader(stream))
    if args.dry_run:
        print(f"DRY RUN: {len(companies)} companies; fiscal years ending in {year}; original statements")
        print("No prediction, model extraction, or estimates. Uncertainty: Needs manual input.")
        print("Reported net income/loss only; total comprehensive income is excluded.")
        for company in companies:
            print(f"  {company['company_id']}: {company['company_name']}")
        print(f"Planned workbook: {destination}")
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
            source = find_original_audited_report(company, year)
            pdf = obtain_pdf(source, company["company_id"], root)
            record = extract_record(company, pdf, source, year)
            validator.validate(record)
            if record["fiscal_year"] != year or record["company_id"] != company["company_id"]:
                raise ValueError("Extracted company or fiscal year does not match the request.")
            record = prepare_record(record, year)
        except Exception as error:
            record = pending_record(company, year, f"{type(error).__name__}: {error}")
        records.append(record)
        outcomes.append({"company_id": company["company_id"], "status": record["status"],
                         "review_notes": record["review_notes"],
                         "metrics": {key: {"status": record[key]["status"],
                                            "review_note": record[key]["review_note"]}
                                     for key in ("revenue", "net_income", "total_assets")}})
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(outcomes, indent=2), encoding="utf-8")
    if records:
        write_workbook(records, destination, companies)
    ready = sum(record["status"] == "ready" for record in records)
    print(f"Ready: {ready}/{len(companies)}; run report: {report}")
    return 0 if companies and ready == len(companies) else 1


if __name__ == "__main__":
    raise SystemExit(main())
