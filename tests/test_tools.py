"""MCP tool tests: every one of the 24 tools is executed against the sample database."""
import csv
import unittest
from pathlib import Path

from mcp_servers import registry
from tests.helpers import DemoDataTestCase
from utils.validators import ToolError

EXPECTED_TOOLS = {
    "get_data_overview", "get_all_sales", "get_sales_by_date_range", "calculate_total_revenue",
    "calculate_monthly_sales", "find_best_selling_products", "find_worst_selling_products",
    "analyze_product_performance", "calculate_average_order_value", "identify_low_performing_products",
    "generate_sales_summary", "export_sales_report", "compare_periods", "get_revenue_by_category",
    "list_products", "search_customers", "get_customer_details", "get_top_customers",
    "create_business_insights", "generate_report", "get_integration_status", "send_report_to_slack",
    "sync_sales_to_google_sheets", "get_crm_contact",
}


class ToolTests(DemoDataTestCase):
    def test_registry_has_all_24_tools_with_schemas(self):
        names = {t["name"] for t in registry.describe()}
        self.assertEqual(names, EXPECTED_TOOLS)
        for tool in registry.describe():
            self.assertTrue(tool["description"])
            self.assertEqual(tool["input_schema"]["type"], "object")

    def test_known_numbers_for_last_month(self):
        r = registry.call("calculate_total_revenue", {"period": "last_month"})
        self.assertEqual(r["period"], "October 2026")
        self.assertEqual(r["total_revenue"], 48497.15)
        self.assertEqual(r["orders"], 168)

    def test_monthly_sales(self):
        r = registry.call("calculate_monthly_sales", {"months": 3})
        self.assertEqual([m["month"] for m in r["months"]], ["2026-09", "2026-10", "2026-11"])
        self.assertTrue(r["months"][-1]["partial"])
        self.assertFalse(r["months"][0]["partial"])

    def test_best_and_worst_products(self):
        best = registry.call("find_best_selling_products", {"period": "last_month", "top_n": 3})
        self.assertEqual(best["products"][0]["product_name"], "Nova X Smartphone")
        revenues = [p["revenue"] for p in best["products"]]
        self.assertEqual(revenues, sorted(revenues, reverse=True))
        worst = registry.call("find_worst_selling_products", {"period": "last_month", "top_n": 3})
        self.assertEqual(worst["products"][0]["revenue"], 0)
        units = registry.call("find_best_selling_products", {"metric": "units", "top_n": 2})
        self.assertEqual(units["metric"], "units")

    def test_product_analysis(self):
        r = registry.call("analyze_product_performance", {"product_name": "nova x"})
        self.assertEqual(r["product"], "Nova X Smartphone")
        self.assertIn(r["verdict"], ("Top performer", "Mid-range performer", "Low performer"))
        with self.assertRaises(ToolError):
            registry.call("analyze_product_performance", {"product_name": "does not exist"})

    def test_aov_low_performers_summary(self):
        aov = registry.call("calculate_average_order_value", {"period": "last_month"})
        self.assertAlmostEqual(aov["average_order_value"], 48497.15 / 168, places=2)
        low = registry.call("identify_low_performing_products", {"period": "last_month"})
        self.assertGreater(low["count"], 0)
        summary = registry.call("generate_sales_summary", {"period": "last_month"})
        self.assertEqual(summary["orders"], 168)
        self.assertEqual(summary["vs_previous"]["period"], "September 2026")

    def test_compare_periods_like_for_like(self):
        r = registry.call("compare_periods", {})
        self.assertIsNotNone(r["like_for_like"])
        self.assertIn("revenue", r["change_pct"])

    def test_sales_listing_and_range(self):
        r = registry.call("get_all_sales", {"limit": 5})
        self.assertEqual(r["returned"], 5)
        rng = registry.call("get_sales_by_date_range", {"start_date": "2026-10-01", "end_date": "2026-10-31"})
        self.assertEqual(rng["total_records"], 168)
        with self.assertRaises(ToolError):
            registry.call("get_sales_by_date_range", {"start_date": "2026-10-31", "end_date": "2026-10-01"})

    def test_customers(self):
        found = registry.call("search_customers", {"query": "london"})
        self.assertGreater(found["total_matches"], 0)
        cid = found["customers"][0]["customer_id"]
        detail = registry.call("get_customer_details", {"customer_id": cid})
        self.assertEqual(detail["customer_id"], cid)
        by_email = registry.call("get_customer_details", {"email": detail["email"]})
        self.assertEqual(by_email["name"], detail["name"])
        with self.assertRaises(ToolError):
            registry.call("get_customer_details", {})
        top = registry.call("get_top_customers", {"top_n": 3})
        self.assertEqual(len(top["customers"]), 3)

    def test_category_and_product_list(self):
        r = registry.call("get_revenue_by_category", {"period": "last_month"})
        self.assertAlmostEqual(sum(c["revenue"] for c in r["categories"]), 48497.15, places=1)
        self.assertEqual(registry.call("list_products", {"category": "Phones"})["count"], 3)

    def test_insights(self):
        r = registry.call("create_business_insights", {"period": "last_month"})
        self.assertGreaterEqual(len(r["insights"]), 4)
        for item in r["insights"]:
            self.assertIn(item["type"], ("positive", "warning", "info"))
            self.assertTrue(item["recommendation"])

    def test_csv_export_and_csv_report(self):
        export = registry.call("export_sales_report", {"period": "last_month"})
        with open(export["file_path"], newline="", encoding="utf-8") as handle:
            rows = list(csv.reader(handle))
        self.assertEqual(len(rows) - 1, 168)
        report = registry.call("generate_report", {"period": "last_month", "report_format": "csv"})
        self.assertTrue(Path(report["file_path"]).read_text(encoding="utf-8").startswith("Sales report"))

    def test_pdf_report(self):
        report = registry.call("generate_report", {"period": "last_month", "report_format": "pdf", "title": "Test report"})
        data = Path(report["file_path"]).read_bytes()
        self.assertTrue(data.startswith(b"%PDF"))
        self.assertGreater(len(data), 3000)

    def test_report_for_empty_period_fails_cleanly(self):
        with self.assertRaises(ToolError):
            registry.call("generate_report", {"period": "2020-01"})

    def test_integration_tools_are_labelled_mock(self):
        status = registry.call("get_integration_status", {})
        modes = {i["name"]: i["mode"] for i in status["integrations"]}
        self.assertEqual(modes["Slack"], "mock")
        self.assertEqual(modes["Google Sheets"], "mock")
        self.assertEqual(modes["CRM"], "mock")
        slack = registry.call("send_report_to_slack", {"period": "last_month"})
        self.assertEqual(slack["mode"], "mock")
        self.assertFalse(slack["sent"])
        sheets = registry.call("sync_sales_to_google_sheets", {})
        self.assertEqual(sheets["mode"], "mock")
        self.assertFalse(sheets["synced"])

    def test_crm_mock_lookup(self):
        email = registry.call("get_customer_details", {"customer_id": 1})["email"]
        r = registry.call("get_crm_contact", {"email": email})
        self.assertTrue(r["found"])
        self.assertEqual(r["mode"], "mock")

    def test_bad_input_is_rejected(self):
        for name, args in [("calculate_total_revenue", {"period": "nonsense"}),
                           ("get_all_sales", {"limit": 100000}),
                           ("get_all_sales", {"unknown_arg": 1}),
                           ("calculate_total_revenue", {"start_date": "yesterday"}),
                           ("find_best_selling_products", {"metric": "magic"}),
                           ("generate_report", {"report_format": "exe"}),
                           ("generate_report", {"filename": "../../evil"}),
                           ("not_a_tool", {})]:
            with self.assertRaises(ToolError, msg=f"{name} {args}"):
                registry.call(name, args)


if __name__ == "__main__":
    unittest.main()
