"""Shared test setup: every test class gets its own temporary database and reports folder."""
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

from config import settings
from database import init_db

ANCHOR = date(2026, 11, 23)   # fixed date -> the seeded data (seed 42) is always identical


class DemoDataTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = Path(tempfile.mkdtemp(prefix="mcp_test_"))
        cls._saved = {k: getattr(settings, k) for k in (
            "DB_PATH", "REPORTS_DIR", "SAMPLE_DATA_DIR", "DB_BACKEND", "SLACK_WEBHOOK_URL",
            "GOOGLE_SHEETS_CREDENTIALS_FILE", "GOOGLE_SHEETS_SPREADSHEET_ID", "CRM_BASE_URL", "CRM_API_KEY")}
        settings.DB_PATH = cls._tmp / "test.db"
        settings.REPORTS_DIR = cls._tmp / "reports"
        settings.SAMPLE_DATA_DIR = cls._tmp / "sample_data"
        settings.DB_BACKEND = "sqlite"
        settings.SLACK_WEBHOOK_URL = ""
        settings.GOOGLE_SHEETS_CREDENTIALS_FILE = ""
        settings.GOOGLE_SHEETS_SPREADSHEET_ID = ""
        settings.CRM_BASE_URL = ""
        settings.CRM_API_KEY = ""
        init_db.initialize(reset=True, anchor_date=ANCHOR, db_path=settings.DB_PATH, write_csv=True)

    @classmethod
    def tearDownClass(cls):
        for key, value in cls._saved.items():
            setattr(settings, key, value)
        shutil.rmtree(cls._tmp, ignore_errors=True)
