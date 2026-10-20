import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator, FormatChecker

from financial_pipeline import __main__ as cli
from financial_pipeline.policy import previous_fiscal_year
from financial_pipeline.reference import parse_amount, read_example
from financial_pipeline.spreadsheet import output_value
from financial_pipeline.validation import MANUAL, METRICS, pending_record, prepare_record


ROOT = Path(__file__).resolve().parent.parent


def reviewed_fixture():
    """Synthetic test data only. Never an expected-result financial record."""
    record = pending_record({"company_id": "test", "company_name": "Synthetic"}, 2025, "")
    record.update(fiscal_year_end="2025-09-30", publication_date="2026-01-15",
                  audited=True, original_verified=True, auditor_evidence_pdf_page=2,
                  pdf_filename="synthetic.pdf", status="ready", net_income_basis="consolidated_total",
                  net_income_measure="reported_net_income",
                  net_income_derivation="Synthetic fixture: copied reported net loss on PDF page 4.")
    for metric in METRICS:
        record[metric].update(value=-25 if metric == "net_income" else 0, currency="CAD",
                              unit_multiplier=1000, pdf_page=4, source_label=metric,
                              status="ready", review_note="")
    return record


class PolicyTests(unittest.TestCase):
    def test_target_year_rolls_over_on_january_first(self):
        self.assertEqual(previous_fiscal_year(date(2026, 12, 31)), 2025)
        self.assertEqual(previous_fiscal_year(date(2027, 1, 1)), 2026)
        self.assertEqual(previous_fiscal_year(date(2027, 10, 20)), 2026)

    def test_pending_record_matches_schema(self):
        schema = json.loads((ROOT / "schemas/financial_record.schema.json").read_text())
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        validator.check_schema(schema)
        validator.validate(pending_record({"company_id": "test", "company_name": "Synthetic"}, 2025, "No PDF"))
        validator.validate(reviewed_fixture())

    def test_fiscal_year_end_not_publication_year(self):
        self.assertEqual(prepare_record(reviewed_fixture(), 2025)["status"], "ready")
        record = reviewed_fixture()
        record["fiscal_year_end"] = "2026-01-31"
        self.assertTrue(all(prepare_record(record, 2025)[key]["value"] is None for key in METRICS))

    def test_restatement_or_unverified_original_is_rejected(self):
        record = reviewed_fixture()
        record["original_verified"] = False
        self.assertEqual(prepare_record(record, 2025)["status"], MANUAL)
        self.assertIsNone(prepare_record(record, 2025)["revenue"]["value"])

    def test_uncertain_metric_does_not_erase_other_metrics(self):
        record = reviewed_fixture()
        record["revenue"].update(status=MANUAL, review_note="Ambiguous statement label", value=123)
        result = prepare_record(record, 2025)
        self.assertIsNone(result["revenue"]["value"])
        self.assertEqual(output_value(result["revenue"]), "Needs manual input")
        self.assertEqual(result["net_income"]["value"], -25)
        self.assertEqual(result["total_assets"]["value"], 0)

    def test_zero_and_losses_are_preserved(self):
        result = prepare_record(reviewed_fixture(), 2025)
        self.assertEqual(output_value(result["revenue"]), 0)
        self.assertEqual(output_value(result["net_income"]), -25)

    def test_missing_derivation_only_blocks_net_income(self):
        record = reviewed_fixture()
        record["net_income_derivation"] = ""
        result = prepare_record(record, 2025)
        self.assertIsNone(result["net_income"]["value"])
        self.assertEqual(result["revenue"]["status"], "ready")

    def test_comprehensive_and_unresolved_measures_require_manual_input(self):
        for measure in ("total_comprehensive_income", "other_comprehensive_income", "other", "unresolved"):
            with self.subTest(measure=measure):
                record = reviewed_fixture()
                record["net_income_measure"] = measure
                result = prepare_record(record, 2025)
                self.assertIsNone(result["net_income"]["value"])
                self.assertEqual(result["net_income"]["status"], MANUAL)
                self.assertEqual(result["revenue"]["status"], "ready")

    def test_comprehensive_source_label_cannot_be_misclassified_as_net_income(self):
        for label in ("Total comprehensive income", "TOTAL COMPREHENSIVE LOSS", "Other comprehensive income"):
            with self.subTest(label=label):
                record = reviewed_fixture()
                record["net_income"]["source_label"] = label
                self.assertIsNone(prepare_record(record, 2025)["net_income"]["value"])

    def test_attributable_subtotal_does_not_replace_reported_group_net_income(self):
        record = reviewed_fixture()
        record["net_income_basis"] = "attributable_to_owners"
        self.assertIsNone(prepare_record(record, 2025)["net_income"]["value"])

    def test_missing_currency_blocks_value(self):
        record = reviewed_fixture()
        record["total_assets"]["currency"] = None
        self.assertIsNone(prepare_record(record, 2025)["total_assets"]["value"])

    def test_nan_cannot_reach_output(self):
        record = reviewed_fixture()
        record["revenue"]["value"] = float("nan")
        self.assertIsNone(prepare_record(record, 2025)["revenue"]["value"])

    def test_units_convert_without_currency_conversion(self):
        item = reviewed_fixture()["revenue"]
        item.update(value=1234500, unit_multiplier=1)
        self.assertEqual(output_value(item), 1234.5)

    def test_reference_parentheses_and_footnotes(self):
        amount = parse_amount("($86,141) (2)")
        self.assertEqual(amount["value"], -86141)
        self.assertEqual(amount["footnote_markers"], ["2"])
        self.assertEqual(parse_amount("($624)")["footnote_markers"], [])
        self.assertIsNone(parse_amount("NP")["value"])

    def test_all_25_reference_companies_and_years_imported(self):
        examples = read_example(ROOT / "inputs/reference/output_example.csv")
        self.assertEqual(len(examples), 25)
        self.assertEqual(examples[0]["expected"]["revenue"]["2025"]["value"], 70787)
        self.assertEqual(examples[0]["expected"]["revenue"]["2024"]["value"], 64990)
        self.assertEqual(examples[1]["company_name"], "Orion Digital Corp.")
        self.assertTrue(all(example["currency"] is None for example in examples))

    def test_batch_keeps_every_company_when_discovery_is_unimplemented(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            root = Path(directory)
            config = json.loads((ROOT / "config.json").read_text())
            config.update(companies_csv=str(ROOT / "inputs/companies.csv"),
                          output_xlsx="synthetic.xlsx", run_report="run_report.json")
            config_path = root / "config.json"
            config_path.write_text(json.dumps(config))
            with patch("sys.argv", ["financial_pipeline", "--config", str(config_path)]), \
                 patch.object(cli, "find_original_audited_report", side_effect=NotImplementedError("TODO")), \
                 patch.object(cli, "write_workbook") as writer, patch("builtins.print"):
                self.assertEqual(cli.main(), 1)
            exported_records = writer.call_args.args[0]
            self.assertEqual(len(exported_records), 25)
            self.assertTrue(all(record["status"] == MANUAL for record in exported_records))
            outcomes = json.loads((root / "run_report.json").read_text())
            self.assertEqual(len(outcomes), 25)
            self.assertIn("NotImplementedError", outcomes[0]["review_notes"])

    def test_next_year_batch_uses_only_2026_and_year_specific_output_paths(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            root = Path(directory)
            config = json.loads((ROOT / "config.json").read_text())
            config["companies_csv"] = str(ROOT / "inputs/companies.csv")
            config_path = root / "config.json"
            config_path.write_text(json.dumps(config))
            with patch("sys.argv", ["financial_pipeline", "--config", str(config_path)]), \
                 patch.object(cli, "previous_fiscal_year", return_value=2026), \
                 patch.object(cli, "find_original_audited_report", side_effect=NotImplementedError("TODO")) as discover, \
                 patch.object(cli, "write_workbook") as writer, patch("builtins.print"):
                self.assertEqual(cli.main(), 1)
            self.assertTrue(all(call.args[1] == 2026 for call in discover.call_args_list))
            self.assertTrue(all(record["fiscal_year"] == 2026 for record in writer.call_args.args[0]))
            self.assertEqual(writer.call_args.args[1].name, "financials_2026.xlsx")
            self.assertTrue((root / "outputs/run_report_2026.json").exists())


if __name__ == "__main__":
    unittest.main()
