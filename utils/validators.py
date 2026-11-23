"""Input validation helpers.

Every value that comes from the user or from the AI model is checked here
before it is used. Invalid input raises ``ToolError`` with a clear message.
"""
import re
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

from config import settings


class ToolError(ValueError):
    """Raised when a tool gets bad input or cannot complete safely."""


_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_FILENAME_STEM = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_\-]{0,80}$")
_EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,255}\.[^@\s]{2,}$")
ALLOWED_REPORT_EXTENSIONS = (".pdf", ".csv")


def validate_date(value, field: str = "date") -> date:
    """Accept a date, datetime or 'YYYY-MM-DD' string."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        raise ToolError(f"{field} must be a text value in YYYY-MM-DD format.")
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError:
        raise ToolError(
            f"{field} must use YYYY-MM-DD format (example: 2026-10-31), got {value!r}."
        )


def validate_int(value, field: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool):
        raise ToolError(f"{field} must be a whole number.")
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ToolError(f"{field} must be a whole number, got {value!r}.")
    if not minimum <= number <= maximum:
        raise ToolError(f"{field} must be between {minimum} and {maximum}, got {number}.")
    return number


def validate_float(value, field: str, minimum: float, maximum: float) -> float:
    if isinstance(value, bool):
        raise ToolError(f"{field} must be a number.")
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ToolError(f"{field} must be a number, got {value!r}.")
    if not minimum <= number <= maximum:
        raise ToolError(f"{field} must be between {minimum} and {maximum}, got {number}.")
    return number


def validate_text(value, field: str, max_length: int = 100, allow_empty: bool = False) -> str:
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise ToolError(f"{field} must be text.")
    cleaned = value.strip()
    if _CONTROL_CHARS.search(cleaned):
        raise ToolError(f"{field} contains invalid control characters.")
    if not cleaned and not allow_empty:
        raise ToolError(f"{field} must not be empty.")
    if len(cleaned) > max_length:
        raise ToolError(f"{field} is too long (maximum {max_length} characters).")
    return cleaned


def validate_choice(value, field: str, choices: Iterable[str]) -> str:
    choices = tuple(choices)
    text = str(value).strip().lower()
    if text not in choices:
        raise ToolError(f"{field} must be one of: {', '.join(choices)}. Got {value!r}.")
    return text


def validate_email(value, field: str = "email") -> str:
    text = validate_text(value, field, max_length=254).lower()
    if not _EMAIL.match(text):
        raise ToolError(f"{field} does not look like a valid email address: {value!r}.")
    return text


def validate_user_query(text) -> str:
    """Validate a chat message typed by the user."""
    return validate_text(text, "Question", max_length=settings.MAX_QUERY_LENGTH)


def safe_report_path(filename: str) -> Path:
    """Return a path inside the reports folder; reject anything suspicious."""
    name = validate_text(filename, "filename", max_length=90)
    path = Path(name)
    if path.suffix.lower() not in ALLOWED_REPORT_EXTENSIONS:
        raise ToolError("Only .pdf and .csv report files are allowed.")
    if not _FILENAME_STEM.match(path.stem) or path.name != name:
        raise ToolError(
            "filename may only contain letters, numbers, '_' and '-' (no folders or spaces)."
        )
    reports_dir = Path(settings.REPORTS_DIR)
    reports_dir.mkdir(parents=True, exist_ok=True)
    target = (reports_dir / name).resolve()
    if target.parent != reports_dir.resolve():
        raise ToolError("Report files must stay inside the reports folder.")
    return target


def is_within_reports(path) -> bool:
    """True when ``path`` is a file located inside the reports folder."""
    try:
        resolved = Path(path).resolve()
        return resolved.parent == Path(settings.REPORTS_DIR).resolve() and resolved.is_file()
    except (OSError, ValueError):
        return False
