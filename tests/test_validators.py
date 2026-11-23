"""Input validation tests."""
import unittest

from utils.dates import resolve_period
from utils.validators import (ToolError, safe_report_path, validate_choice, validate_date, validate_email,
                              validate_int, validate_text, validate_user_query)
from tests.helpers import ANCHOR, DemoDataTestCase


class ValidatorTests(DemoDataTestCase):
    def test_date(self):
        self.assertEqual(str(validate_date("2026-10-31")), "2026-10-31")
        for bad in ("31/10/2026", "2026-13-01", "", 5):
            with self.assertRaises(ToolError):
                validate_date(bad)

    def test_int_limits(self):
        self.assertEqual(validate_int("5", "n", 1, 10), 5)
        for bad in (0, 11, "abc", True):
            with self.assertRaises(ToolError):
                validate_int(bad, "n", 1, 10)

    def test_text_and_query(self):
        self.assertEqual(validate_text("  hi  ", "x"), "hi")
        with self.assertRaises(ToolError):
            validate_text("bad\x00text", "x")
        with self.assertRaises(ToolError):
            validate_user_query("x" * 5000)
        with self.assertRaises(ToolError):
            validate_user_query("   ")

    def test_choice_and_email(self):
        self.assertEqual(validate_choice("PDF", "f", ("pdf", "csv")), "pdf")
        with self.assertRaises(ToolError):
            validate_choice("exe", "f", ("pdf", "csv"))
        self.assertEqual(validate_email("A@Example.com"), "a@example.com")
        with self.assertRaises(ToolError):
            validate_email("not-an-email")

    def test_report_path_is_safe(self):
        from config import settings
        path = safe_report_path("report_1.pdf")
        self.assertEqual(path.parent, settings.REPORTS_DIR.resolve())
        for bad in ("../evil.pdf", "a/b.pdf", "report.exe", "my report.pdf", "..\\evil.csv"):
            with self.assertRaises(ToolError):
                safe_report_path(bad)

    def test_periods(self):
        last = resolve_period("last_month", ANCHOR)
        self.assertEqual((str(last.start), str(last.end)), ("2026-10-01", "2026-10-31"))
        this = resolve_period("this_month", ANCHOR)
        self.assertEqual(str(this.start), "2026-11-01")
        self.assertEqual(str(this.previous().start), "2026-10-01")
        self.assertEqual(resolve_period("2026-02", ANCHOR).end.day, 28)
        self.assertEqual(str(resolve_period("last_30_days", ANCHOR).start), "2026-10-25")
        self.assertTrue(resolve_period("all", ANCHOR).is_all)
        with self.assertRaises(ToolError):
            resolve_period("someday", ANCHOR)
        with self.assertRaises(ToolError):
            resolve_period("2026-13", ANCHOR)


if __name__ == "__main__":
    unittest.main()
