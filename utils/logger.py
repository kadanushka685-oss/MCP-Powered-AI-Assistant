"""Small logging helper: writes to logs/app.log and warnings to stderr.

Logging goes to stderr (never stdout) because the MCP server talks to its
client over stdout and any stray print would corrupt the protocol.
"""
import logging
import sys

from config import settings

_configured = False


def get_logger(name: str) -> logging.Logger:
    global _configured
    root = logging.getLogger("mcp_assistant")
    if not _configured:
        root.setLevel(logging.INFO)
        root.propagate = False
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        stream = logging.StreamHandler(sys.stderr)
        stream.setLevel(logging.WARNING)
        stream.setFormatter(formatter)
        root.addHandler(stream)
        try:
            settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(settings.LOG_DIR / "app.log", encoding="utf-8")
            file_handler.setFormatter(formatter)
            root.addHandler(file_handler)
        except OSError:
            pass  # logging to file is optional
        _configured = True
    return logging.getLogger(f"mcp_assistant.{name}")
