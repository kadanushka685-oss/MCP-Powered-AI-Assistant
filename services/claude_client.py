"""Talks to the Anthropic Claude API using *tool use*.

How it works (the "agent loop"):
1. We send the user's question + the list of discovered MCP tools to Claude.
2. Claude replies either with a final answer or with tool_use requests.
3. We run the requested tools (through the executor) and send the results back.
4. Repeat until Claude gives a final answer (maximum MAX_TOOL_ROUNDS rounds).

Claude never touches the database itself. It can only ask for approved tools.
"""
import json
from typing import List, Tuple

from config import settings
from utils.logger import get_logger
from utils.validators import ToolError

log = get_logger("claude")

SYSTEM_PROMPT = """You are a business analytics assistant inside a sales dashboard.
Rules:
- Use the provided tools to get data. Never invent numbers, products or customers.
- Relative dates (last month, this month) are relative to the latest sale date: {latest}.
- If a tool returns an error, explain it simply and try a corrected call once.
- When you create a report file, tell the user the file name and that it is on the Reports page.
- Answer clearly in Markdown with short sections and tables where useful. Mention the period you analysed.
- Currency is US dollars. Keep answers concise and practical."""


class ClaudeClient:
    def __init__(self, api_key: str = "", model: str = "") -> None:
        try:
            import anthropic
        except ImportError:
            raise ToolError("The 'anthropic' package is not installed. Run: pip install anthropic")
        self._anthropic = anthropic
        self.client = anthropic.Anthropic(api_key=api_key or settings.ANTHROPIC_API_KEY)
        self.model = model or settings.CLAUDE_MODEL

    @staticmethod
    def _to_claude_tools(tools: List[dict]) -> List[dict]:
        return [{"name": t["name"], "description": t["description"], "input_schema": t["input_schema"]} for t in tools]

    def chat(self, question: str, history: List[dict], tools: List[dict], executor,
             latest_date: str) -> Tuple[str, List[dict]]:
        """Run the agent loop. Returns (answer text, tool-call records)."""
        messages = [m for m in history[-10:] if m.get("role") in ("user", "assistant") and m.get("content")]
        messages = [{"role": m["role"], "content": m["content"]} for m in messages]
        messages.append({"role": "user", "content": question})
        claude_tools = self._to_claude_tools(tools)
        records: List[dict] = []

        for _ in range(settings.MAX_TOOL_ROUNDS):
            try:
                response = self.client.messages.create(
                    model=self.model, max_tokens=1500,
                    system=SYSTEM_PROMPT.format(latest=latest_date),
                    tools=claude_tools, messages=messages)
            except Exception as exc:  # noqa: BLE001
                log.error("Claude API call failed: %s", type(exc).__name__)
                raise ToolError(f"Claude API call failed ({type(exc).__name__}). Check your API key, model name and internet connection.")

            tool_uses = [block for block in response.content if block.type == "tool_use"]
            if response.stop_reason != "tool_use" or not tool_uses:
                text = "\n".join(b.text for b in response.content if b.type == "text").strip()
                return text or "I could not produce an answer.", records

            messages.append({"role": "assistant", "content": response.content})
            results = []
            for block in tool_uses:
                record = executor.call(block.name, dict(block.input or {}))
                records.append(record)
                if record["status"] == "success":
                    payload = json.dumps(record["result"], default=str)[: settings.MAX_TOOL_RESULT_CHARS]
                    results.append({"type": "tool_result", "tool_use_id": block.id, "content": payload})
                else:
                    results.append({"type": "tool_result", "tool_use_id": block.id,
                                    "content": record["error"], "is_error": True})
            messages.append({"role": "user", "content": results})
        return ("I reached the maximum number of tool steps. Please ask a more specific question.", records)
