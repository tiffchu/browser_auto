"""Validate reviewed source transcriptions and create an auditable export payload.

This is the reviewed 25-company test, not automatic statement discovery/extraction.
Reproduction: .venv/Scripts/python.exe scripts/prepare_test_run.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from jsonschema import Draft202012Validator, FormatChecker
from financial_pipeline.currency import cad_amount, rank_by_revenue, year_end_usdcad
from financial_pipeline.reference import read_example
from financial_pipeline.validation import METRICS, pending_record, prepare_record


def main():
    companies = read_example(ROOT / "inputs/test_run_2025.csv")
    reviewed = json.loads((ROOT / "inputs/test_run_2025_reviewed.json").read_text())
    sources = {r["input_rank"]: r for r in json.loads((ROOT / "inputs/test_run_2025_sources.json").read_text())}
    observations = json.loads((ROOT / "data/test_run_2025/bank_of_canada_fx.json").read_text())
    fx_date, rate = year_end_usdcad(observations, 2025)
    # This reviewed dataset is explicitly frozen to 2025. Do not relabel it next year.
    assert {c["rank"] for c in companies} == {r["input_rank"] for r in reviewed}
    assert len(companies) == len(reviewed) == 25
    validator = Draft202012Validator(json.loads((ROOT / "schemas/financial_record.schema.json").read_text()), format_checker=FormatChecker())
    by_rank = {r["input_rank"]: r for r in reviewed}
    rows = []
    for company in companies:
        raw = by_rank[company["rank"]]
        canonical = sources[company["rank"]]["report_url"]
        url = canonical
        if company["rank"] == 2:
            url = "https://www.sec.gov/Archives/edgar/data/1397187/000139718725000013/lulu-20250202.htm"
        elif company["rank"] == 10:
            url = "https://www.methanex.com/wp-content/uploads/2025-Annual-Report-Financial-Statements-Only.pdf"
            canonical = url
        elif company["rank"] == 24:
            url = "https://financialfilings.com/filings/canaccord-genuity-group-inc/annual-report/2025/13799721/"
        record = pending_record(company, 2025, "")
        record.update(fiscal_year_end=raw["fiscal_year_end"], auditor_report_date=raw["audit_date"],
                      auditor_evidence_pdf_page=raw["audit_page"], auditor_evidence_locator=raw.get("audit_locator"),
                      audited=True, original_verified=True, source_url=url,
                      pdf_filename=f"company_{company['rank']:02d}." + ("html" if raw.get("income_locator") else "pdf"),
                      status="ready", review_notes=raw["review_notes"],
                      net_income_measure="reported_net_income", net_income_basis="consolidated_total",
                      net_income_derivation=raw["net_income_derivation"])
        for metric in METRICS:
            location = "assets" if metric == "total_assets" else "income"
            label = "assets" if metric == "total_assets" else metric
            record[metric].update(value=raw[metric], currency=raw["currency"], unit_multiplier=raw["unit_multiplier"],
                                  pdf_page=raw[location + "_page"], source_locator=raw.get(location + "_locator"),
                                  source_label=raw[label + "_label"], status="ready", review_note="")
        validator.validate(record)
        record = prepare_record(record, 2025)
        rows.append({**record, "input_rank":company["rank"], "stock_symbol":company["stock_symbol"],
                     "original_report_url":canonical})
    rows = rank_by_revenue(rows, rate)
    for row in rows:
        row["cad_values"] = {key: float(value) if (value := cad_amount(row[key], rate)) is not None else None for key in METRICS}
        row["converted_from_usd"] = row["revenue"]["currency"] == "USD"
    payload = {"year":2025,"fx_date":fx_date,"usdcad":str(rate),
               "fx_source_url":"https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json?start_date=2025-12-20&end_date=2025-12-31",
               "method":"Reviewed original annual consolidated statements; no estimates. Fiscal years ending in 2025. All USD metrics use the calendar year-end Bank of Canada rate. Full-dollar output retains the precision of the reported source.",
               "records":rows}
    output = ROOT / "outputs"
    output.mkdir(exist_ok=True)
    (output / "test_run_2025_records.json").write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"companies":len(rows),"ready":sum(r["status"]=="ready" for r in rows),
                      "usd_converted":sum(r["converted_from_usd"] for r in rows),"fx_date":fx_date,"rate":str(rate),
                      "top_five":[[r["revenue_rank"],r["company_name"],r["cad_values"]["revenue"]] for r in rows[:5]]}))


if __name__ == "__main__":
    main()
