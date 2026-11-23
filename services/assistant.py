"""The assistant: decides HOW to answer (Claude or demo mode) and runs the tools."""
from dataclasses import dataclass, field
from typing import List, Optional

from config import settings
from database import repository
from services.intent_router import HELP_TEXT, DemoPlanner
from services.response_formatter import format_record
from utils.logger import get_logger
from utils.validators import ToolError, validate_user_query

log = get_logger("assistant")


@dataclass
class AssistantReply:
    text: str
    records: List[dict] = field(default_factory=list)
    mode: str = "demo"                      # "demo" or "claude"
    warnings: List[str] = field(default_factory=list)


class SalesAssistant:
    def __init__(self, executor, claude_client=None) -> None:
        self.executor = executor
        self.claude = claude_client

    def ask(self, question: str, history: Optional[List[dict]] = None) -> AssistantReply:
        try:
            question = validate_user_query(question)
        except ToolError as exc:
            return AssistantReply(f"I can't use that input: {exc}")
        try:
            tools = self.executor.list_tools()           # dynamic tool discovery
        except ToolError as exc:
            return AssistantReply(f"I could not discover the tools: {exc}")

        warnings: List[str] = []
        if self.claude is not None and not settings.is_demo_mode():
            try:
                latest = str(repository.get_reference_date())
                text, records = self.claude.chat(question, history or [], tools, self.executor, latest)
                return AssistantReply(text, records, mode="claude")
            except ToolError as exc:
                warnings.append(f"{exc} Falling back to demo mode for this answer.")
                log.warning("Claude path failed: %s", exc)
        return self._demo_answer(question, tools, warnings)

    def _demo_answer(self, question: str, tools: List[dict], warnings: List[str]) -> AssistantReply:
        try:
            names = repository.get_products_df()["name"].tolist()
            reference = repository.get_reference_date()
        except Exception as exc:  # noqa: BLE001
            return AssistantReply(f"The database is not available: {exc}", warnings=warnings)
        steps = DemoPlanner(names, reference).plan(question, tools)
        if not steps:
            return AssistantReply(HELP_TEXT, mode="demo", warnings=warnings)
        records = [self.executor.call(step.tool, step.arguments) for step in steps]
        used = ", ".join(f"`{s.tool}`" for s in steps)
        intro = f"_Demo mode: I matched your question to these tools: {used}._"
        body = "\n\n".join(format_record(r) for r in records)
        return AssistantReply(f"{intro}\n\n{body}", records, mode="demo", warnings=warnings)
