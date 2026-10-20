import unittest
from decimal import Decimal
from financial_pipeline.currency import cad_amount, rank_by_revenue, year_end_usdcad


def metric(value, currency="USD", units=1000, status="ready"):
    return {"value":value,"currency":currency,"unit_multiplier":units,"status":status}


class CurrencyTests(unittest.TestCase):
    def test_full_units_and_loss_conversion(self):
        self.assertEqual(cad_amount(metric(-1234), "1.3706"), Decimal("-1691320.4"))
        self.assertEqual(cad_amount(metric(5.2,"CAD",1000000)), Decimal("5200000.0"))
        self.assertEqual(cad_amount(metric(0), "1.3706"), Decimal(0))

    def test_missing_fx_currency_and_uncertain_values_stay_manual(self):
        self.assertIsNone(cad_amount(metric(12)))
        self.assertIsNone(cad_amount(metric(12,"EUR"), "1.3706"))
        self.assertIsNone(cad_amount(metric(12,status="needs_manual_input"),"1.3706"))
        self.assertIsNone(cad_amount(metric(None),"1.3706"))
        self.assertIsNone(cad_amount(metric(12),0))

    def test_rank_uses_converted_revenue_keeps_missing_and_ties(self):
        records=[{"company_name":"CAD","revenue":metric(130,"CAD")},
                 {"company_name":"USD","revenue":metric(100)},
                 {"company_name":"Missing","revenue":metric(None)},
                 {"company_name":"Tied","revenue":metric(130,"CAD")}]
        rows=rank_by_revenue(records,"1.3706")
        self.assertEqual([r["company_name"] for r in rows],["USD","CAD","Tied","Missing"])
        self.assertEqual([r["revenue_rank"] for r in rows],[1,2,2,None])
        changed=rank_by_revenue(records,"1.0")
        self.assertEqual([r["company_name"] for r in changed],["CAD","Tied","USD","Missing"])

    def test_year_end_uses_last_published_business_day_and_rejects_wrong_year(self):
        observations={"observations":[{"d":"2025-12-31","FXUSDCAD":{"v":"1.3706"}},
                                      {"d":"2026-01-02","FXUSDCAD":{"v":"1.9"}}]}
        self.assertEqual(year_end_usdcad(observations,2025),("2025-12-31",Decimal("1.3706")))
        with self.assertRaises(ValueError):
            year_end_usdcad(observations,2024)
        self.assertEqual(year_end_usdcad({"observations":[{"d":"2022-12-30","FXUSDCAD":{"v":"1.3544"}}]},2022)[0],"2022-12-30")
