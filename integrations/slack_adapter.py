"""Slack adapter. LIVE = incoming webhook, MOCK = local outbox file."""
import json
import urllib.error
import urllib.request
from datetime import datetime
from typing import Optional

from config import settings
from integrations.base import IntegrationAdapter
from utils.validators import ToolError


class SlackAdapter(IntegrationAdapter):
    name = "Slack"

    def __init__(self, webhook_url: Optional[str] = None) -> None:
        url = settings.SLACK_WEBHOOK_URL if webhook_url is None else webhook_url
        self.webhook_url = url.strip()

    @property
    def is_live(self) -> bool:
        return self.webhook_url.startswith("https://hooks.slack.com/")

    @property
    def outbox_path(self):
        return settings.REPORTS_DIR / "mock_slack_outbox.jsonl"

    def status(self) -> dict:
        if self.is_live:
            return {"name": self.name, "mode": "live", "detail": "Webhook configured. Messages are really sent to Slack."}
        return {"name": self.name, "mode": "mock",
                "detail": "No SLACK_WEBHOOK_URL set. Messages are saved to a local file only; nothing is sent to Slack."}

    def send_message(self, text: str, channel: Optional[str] = None) -> dict:
        if not text or not text.strip():
            raise ToolError("Slack message must not be empty.")
        text = text.strip()[:3000]
        if self.is_live:
            payload = {"text": text}
            if channel:
                payload["channel"] = channel
            request = urllib.request.Request(
                self.webhook_url, data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}, method="POST")
            try:
                with urllib.request.urlopen(request, timeout=10) as response:
                    ok = response.status == 200
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                raise ToolError(f"Slack request failed: {exc}")
            return {"mode": "live", "sent": ok, "detail": "Message sent to Slack." if ok else "Slack rejected the message."}
        settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        entry = {"time": datetime.now().isoformat(timespec="seconds"), "channel": channel or "#sales", "text": text}
        with open(self.outbox_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
        return {"mode": "mock", "sent": False,
                "detail": f"MOCK: message saved to {self.outbox_path.name}. Nothing was sent to Slack."}

    def read_outbox(self, limit: int = 10) -> list:
        if not self.outbox_path.exists():
            return []
        lines = self.outbox_path.read_text(encoding="utf-8").strip().splitlines()
        return [json.loads(line) for line in lines[-limit:]][::-1]
