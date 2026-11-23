"""Central configuration for the whole project.

Every setting is read from environment variables (or from a local ``.env``
file) so that no secret is ever written inside the source code.
Other modules should do ``from config import settings`` and then read
``settings.SOMETHING`` at call time (this also makes the settings easy to
override in unit tests).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _env_path(name: str, default: Path) -> Path:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    path = Path(raw)
    return path if path.is_absolute() else BASE_DIR / path


# ---------------------------------------------------------------- general
APP_NAME = "MCP-Powered AI Assistant"
APP_TAGLINE = "Enterprise tool integration and workflow automation"
CURRENCY_SYMBOL = "$"

# ------------------------------------------------------------------ paths
REPORTS_DIR = BASE_DIR / "reports"
SAMPLE_DATA_DIR = BASE_DIR / "sample_data"
ASSETS_DIR = BASE_DIR / "assets"
LOG_DIR = BASE_DIR / "logs"

# --------------------------------------------------------------- database
# "sqlite" (default, zero setup) or "postgres" (optional, needs DATABASE_URL)
DB_BACKEND = os.getenv("DB_BACKEND", "sqlite").strip().lower()
DB_PATH = _env_path("SQLITE_DB_PATH", BASE_DIR / "database" / "sales.db")
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

# --------------------------------------------------------------------- AI
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5").strip()
FORCE_DEMO_MODE = _env_bool("DEMO_MODE", False)
MAX_TOOL_ROUNDS = 6          # safety limit: how many tool-use loops Claude may run
MAX_QUERY_LENGTH = 500       # safety limit for user questions
MAX_TOOL_RESULT_CHARS = 12000

# ----------------------------------------------------------- integrations
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "").strip()
GOOGLE_SHEETS_CREDENTIALS_FILE = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE", "").strip()
GOOGLE_SHEETS_SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "").strip()
CRM_BASE_URL = os.getenv("CRM_BASE_URL", "").strip()
CRM_API_KEY = os.getenv("CRM_API_KEY", "").strip()


def has_api_key() -> bool:
    """True when a plausible Anthropic API key is configured."""
    key = ANTHROPIC_API_KEY
    return bool(key) and "your" not in key.lower() and len(key) > 20


def is_demo_mode() -> bool:
    """Demo mode = rule-based assistant, no paid API needed."""
    return FORCE_DEMO_MODE or not has_api_key()


def mask_secret(value: str) -> str:
    """Show only the last 4 characters of a secret (for status screens)."""
    if not value:
        return "(not set)"
    return "*" * 8 + value[-4:]
