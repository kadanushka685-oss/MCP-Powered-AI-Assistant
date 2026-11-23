"""Assistant tests: the seven required sample questions (demo mode) plus executor behaviour."""
import unittest
from pathlib import Path

from services.assistant import SalesAssistant
from services.tool_executor import ToolExecutor
from tests.helpers import DemoDataTestCase

# question -> tools that must be used, and text that must appear in the answer
SAMPLE_QUESTIONS = [
    ("Analyze last month's sales.", ["generate_sales_summary", "find_best_selling_products", "create_business_insights"], "October 2026"),
    ("Which product generated the highest revenue?", ["find_best_selling_products"], "Nova X Smartphone"),
    ("Show monthly revenue.", ["calculate_monthly_sales"], "2026-10"),
    ("Find the top 5 selling products.", ["find_best_selling_products"], "Top products"),
    ("Compare this month and last month.", ["compare_periods"], "October 2026"),
    ("Generate a PDF sales report.", ["generate_report"], "Report created"),
    ("Give me business growth suggestions.", ["create_business_insights"], "Action:"),
]


class AssistantTests(DemoDataTestCase):
    def setUp(self):
        self.executor = ToolExecutor()
        self.assistant = SalesAssistant(self.executor)   # no Claude client -> demo mode

    def test_seven_sample_questions(self):
        for question, tools, expected_text in SAMPLE_QUESTIONS:
            with self.subTest(question=question):
                reply = self.assistant.ask(question)
                self.assertEqual(reply.mode, "demo")
                self.assertEqual([r["tool"] for r in reply.records], tools)
                self.assertTrue(all(r["status"] == "success" for r in reply.records), reply.records)
                self.assertIn(expected_text, reply.text)

    def test_example_from_the_brief_creates_a_pdf(self):
        reply = self.assistant.ask("Analyze last month's sales and create a detailed report.")
        tools = [r["tool"] for r in reply.records]
        self.assertEqual(tools[-1], "generate_report")
        self.assertTrue(Path(reply.records[-1]["result"]["file_path"]).read_bytes().startswith(b"%PDF"))

    def test_top_n_and_period_extraction(self):
        reply = self.assistant.ask("Show the top 3 best selling products in October")
        args = reply.records[0]["arguments"]
        self.assertEqual(args["top_n"], 3)
        self.assertEqual(args["period"], "2026-10")

    def test_customer_and_product_questions(self):
        self.assertEqual(self.assistant.ask("Search customers in London").records[0]["tool"], "search_customers")
        self.assertEqual(self.assistant.ask("How is the Nova X Smartphone performing?").records[0]["tool"], "analyze_product_performance")
        self.assertEqual(self.assistant.ask("customer 5").records[0]["tool"], "get_customer_details")

    def test_help_and_unknown_questions_run_no_tools(self):
        for text in ("hello", "xyzzy plugh"):
            reply = self.assistant.ask(text)
            self.assertEqual(reply.records, [])
            self.assertIn("Analyze last month", reply.text)

    def test_invalid_questions_are_handled(self):
        self.assertIn("can't use that input", self.assistant.ask("   ").text)
        self.assertIn("can't use that input", self.assistant.ask("a" * 2000).text)

    def test_history_records_every_call(self):
        self.assistant.ask("Show monthly revenue.")
        self.assertEqual(len(self.executor.history), 1)
        record = self.executor.history[0]
        self.assertEqual(record["status"], "success")
        self.assertIn("duration_ms", record)

    def test_executor_never_raises(self):
        record = self.executor.call("calculate_total_revenue", {"period": "bad"})
        self.assertEqual(record["status"], "error")
        self.assertIn("Unknown period", record["error"])
        record = self.executor.call("drop_everything", {})
        self.assertEqual(record["status"], "error")


if __name__ == "__main__":
    unittest.main()
