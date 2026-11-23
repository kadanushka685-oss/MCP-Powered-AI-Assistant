"""CRM adapter. LIVE = generic REST API, MOCK = sample file sample_data/crm_contacts.csv."""
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

import pandas as pd

from config import settings
from integrations.base import IntegrationAdapter
from utils.validators import ToolError, validate_email


class CRMAdapter(IntegrationAdapter):
    name = "CRM"

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None) -> None:
        self.base_url = (settings.CRM_BASE_URL if base_url is None else base_url).rstrip("/")
        self.api_key = settings.CRM_API_KEY if api_key is None else api_key

    @property
    def is_live(self) -> bool:
        return self.base_url.startswith("https://") and bool(self.api_key)

    def status(self) -> dict:
        if self.is_live:
            return {"name": self.name, "mode": "live",
                    "detail": f"Calling {self.base_url}/contacts (generic REST format; adapt it to your CRM)."}
        return {"name": self.name, "mode": "mock",
                "detail": "No CRM credentials set. Using the SAMPLE file sample_data/crm_contacts.csv, not a real CRM."}

    def get_contact(self, email: str) -> dict:
        email = validate_email(email)
        if self.is_live:
            url = f"{self.base_url}/contacts?{urllib.parse.urlencode({'email': email})}"
            request = urllib.request.Request(url, headers={"Authorization": f"Bearer {self.api_key}"})
            try:
                with urllib.request.urlopen(request, timeout=10) as response:
                    contact = json.loads(response.read().decode("utf-8"))
            except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
                raise ToolError(f"CRM request failed: {exc}")
            return {"mode": "live", "found": bool(contact), "contact": contact}
        path = settings.SAMPLE_DATA_DIR / "crm_contacts.csv"
        if not path.exists():
            raise ToolError("Sample CRM file sample_data/crm_contacts.csv is missing. Run: python -m database.init_db --reset")
        df = pd.read_csv(path)
        match = df[df["email"].str.lower() == email]
        if match.empty:
            return {"mode": "mock", "found": False, "contact": None,
                    "detail": "MOCK CRM (sample file): no contact with that email."}
        return {"mode": "mock", "found": True, "contact": json.loads(match.iloc[0].to_json()),
                "detail": "MOCK CRM: this record comes from the local sample file, not from a real CRM."}
