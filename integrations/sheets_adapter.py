"""Google Sheets adapter. LIVE needs gspread + a service-account file, MOCK writes local CSV files."""
import re
from pathlib import Path
from typing import Optional

import pandas as pd

from config import settings
from integrations.base import IntegrationAdapter
from utils.validators import ToolError


class GoogleSheetsAdapter(IntegrationAdapter):
    name = "Google Sheets"

    def __init__(self, credentials_file: Optional[str] = None, spreadsheet_id: Optional[str] = None) -> None:
        self.credentials_file = settings.GOOGLE_SHEETS_CREDENTIALS_FILE if credentials_file is None else credentials_file
        self.spreadsheet_id = settings.GOOGLE_SHEETS_SPREADSHEET_ID if spreadsheet_id is None else spreadsheet_id

    @property
    def is_live(self) -> bool:
        return bool(self.credentials_file and self.spreadsheet_id and Path(self.credentials_file).is_file())

    @property
    def mock_dir(self) -> Path:
        return settings.REPORTS_DIR / "mock_google_sheets"

    def status(self) -> dict:
        if self.is_live:
            return {"name": self.name, "mode": "live", "detail": "Credentials found. Data is written to your real spreadsheet."}
        return {"name": self.name, "mode": "mock",
                "detail": "No credentials configured. Data is written to local CSV files only; nothing goes to Google."}

    def push_dataframe(self, df: pd.DataFrame, worksheet: str = "Sales Summary") -> dict:
        name = re.sub(r"[^A-Za-z0-9_\- ]", "", worksheet).strip() or "Sheet"
        if self.is_live:
            try:
                import gspread
            except ImportError:
                raise ToolError("Live Google Sheets needs the optional package: pip install gspread")
            try:
                client = gspread.service_account(filename=self.credentials_file)
                book = client.open_by_key(self.spreadsheet_id)
                try:
                    sheet = book.worksheet(name)
                except gspread.WorksheetNotFound:
                    sheet = book.add_worksheet(title=name, rows=max(len(df) + 5, 20), cols=max(len(df.columns), 5))
                rows = [list(df.columns)] + df.astype(object).where(df.notna(), "").values.tolist()
                sheet.clear()
                sheet.update(values=rows, range_name="A1")
            except Exception as exc:  # noqa: BLE001 - gspread raises many error types
                raise ToolError(f"Google Sheets request failed: {exc}")
            return {"mode": "live", "synced": True, "rows": int(len(df)), "worksheet": name,
                    "detail": "Data written to Google Sheets."}
        self.mock_dir.mkdir(parents=True, exist_ok=True)
        path = self.mock_dir / f"{name.replace(' ', '_')}.csv"
        df.to_csv(path, index=False)
        return {"mode": "mock", "synced": False, "rows": int(len(df)), "worksheet": name,
                "detail": f"MOCK: saved to reports/mock_google_sheets/{path.name}. Nothing was sent to Google."}
