"""Integration adapter tests (mock mode) and Claude-client wiring tests with a fake API."""
import json
import unittest
from types import SimpleNamespace

from config import settings
from integrations import get_integrations
from integrations.slack_adapter import SlackAdapter
from services.claude_client import ClaudeClient
from services.tool_executor import ToolExecutor
from tests.helpers import DemoDataTestCase
from utils.validators import ToolError


class IntegrationTests(DemoDataTestCase):
    def test_default_adapters_are_not_live(self):
        adapters = get_integrations()
        for key in ("crm", "sheets", "slack"):
            self.assertFalse(adapters[key].is_live)
            self.assertEqual(adapters[key].status()["mode"], "mock")
        self.assertEqual(adapters["postgres"].status()["mode"], "not configured")

    def test_slack_mock_writes_outbox_only(self):
        slack = SlackAdapter(webhook_url="")
        result = slack.send_message("hello team")
        self.assertEqual((result["mode"], result["sent"]), ("mock", False))
        self.assertEqual(slack.read_outbox()[0]["text"], "hello team")
        with self.assertRaises(ToolError):
            slack.send_message("   ")

    def test_slack_url_must_be_real_slack_host(self):
        self.assertFalse(SlackAdapter(webhook_url="https://evil.example.com/hook").is_live)
        self.assertTrue(SlackAdapter(webhook_url="https://hooks.slack.com/services/T/B/X").is_live)

    def test_demo_mode_without_key(self):
        saved = settings.ANTHROPIC_API_KEY
        settings.ANTHROPIC_API_KEY = ""
        try:
            self.assertTrue(settings.is_demo_mode())
        finally:
            settings.ANTHROPIC_API_KEY = saved

    def test_mask_secret_hides_key(self):
        self.assertNotIn("abcdefgh", settings.mask_secret("sk-ant-abcdefgh1234"))
        self.assertTrue(settings.mask_secret("sk-ant-abcdefgh1234").endswith("1234"))


class _FakeMessages:
    """Pretends to be anthropic's client.messages: first asks for a tool, then answers."""
    def __init__(self):
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            block = SimpleNamespace(type="tool_use", id="toolu_1", name="calculate_total_revenue", input={"period": "last_month"})
            return SimpleNamespace(stop_reason="tool_use", content=[block])
        last = kwargs["messages"][-1]["content"][0]
        revenue = json.loads(last["content"])["total_revenue"]
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=f"Revenue was {revenue}")])


class ClaudeLoopTests(DemoDataTestCase):
    def test_agent_loop_runs_tools_and_returns_answer(self):
        client = ClaudeClient.__new__(ClaudeClient)           # skip the real anthropic import
        client.client = SimpleNamespace(messages=_FakeMessages())
        client.model = "fake-model"
        executor = ToolExecutor()
        text, records = client.chat("How much revenue last month?", [], executor.list_tools(), executor, "2026-11-23")
        self.assertEqual(text, "Revenue was 48497.15")
        self.assertEqual(records[0]["tool"], "calculate_total_revenue")
        self.assertEqual(client._to_claude_tools(executor.list_tools())[0].keys(), {"name", "description", "input_schema"})


if __name__ == "__main__":
    unittest.main()
