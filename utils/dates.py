"""Period handling: turns words like 'last_month' into real date ranges.

"Today" is the latest sale date found in the database (the *reference date*).
For live data that equals today; for the static demo data it keeps phrases
such as "last month" meaningful no matter when you run the project.
"""
import calendar
import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from utils.validators import ToolError

NAMED_PERIODS = (
    "all", "this_month", "last_month", "last_7_days", "last_30_days",
    "last_90_days", "this_year", "last_year",
)
_ALIASES = {
    "current_month": "this_month", "month_to_date": "this_month",
    "previous_month": "last_month", "past_month": "last_month",
    "last_week": "last_7_days", "past_week": "last_7_days",
    "last_quarter": "last_90_days", "ytd": "this_year", "year_to_date": "this_year",
    "all_time": "all", "everything": "all",
}
PERIOD_HELP = (
    "Period name: all, this_month, last_month, last_7_days, last_30_days, "
    "last_90_days, this_year, last_year, or a month like 2026-10."
)


def month_bounds(year: int, month: int):
    return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])


def month_label(day: date) -> str:
    return f"{calendar.month_name[day.month]} {day.year}"


def _previous_month(year: int, month: int):
    return (year, month - 1) if month > 1 else (year - 1, 12)


@dataclass(frozen=True)
class Period:
    key: str
    label: str
    start: Optional[date]
    end: Optional[date]

    @property
    def is_all(self) -> bool:
        return self.start is None and self.end is None

    def previous(self) -> Optional["Period"]:
        """The period right before this one (same length / previous month)."""
        if self.start is None or self.end is None:
            return None
        if self.start.day == 1 and self.end == month_bounds(self.start.year, self.start.month)[1]:
            year, month = _previous_month(self.start.year, self.start.month)
            start, end = month_bounds(year, month)
            return Period(f"{year}-{month:02d}", month_label(start), start, end)
        length = (self.end - self.start).days + 1
        end = self.start - timedelta(days=1)
        start = end - timedelta(days=length - 1)
        return Period("previous", f"Previous {length} days ({start:%b %d} - {end:%b %d, %Y})", start, end)


def resolve_period(period: Optional[str], ref: date) -> Period:
    """Convert a period name into a ``Period`` relative to the reference date."""
    key = (period or "all").strip().lower().replace(" ", "_")
    key = _ALIASES.get(key, key)

    match = re.fullmatch(r"(\d{4})-(\d{2})", key)
    if match:
        year, month = int(match.group(1)), int(match.group(2))
        if not 1 <= month <= 12 or year < 1990:
            raise ToolError(f"Invalid month {key!r}. Use YYYY-MM, for example 2026-10.")
        start, end = month_bounds(year, month)
        return Period(key, month_label(start), start, end)

    if key == "all":
        return Period("all", "All time", None, None)
    if key == "this_month":
        start, end = month_bounds(ref.year, ref.month)
        suffix = " (month to date)" if ref < end else ""
        return Period(key, month_label(start) + suffix, start, end)
    if key == "last_month":
        year, month = _previous_month(ref.year, ref.month)
        start, end = month_bounds(year, month)
        return Period(key, month_label(start), start, end)
    if key in ("last_7_days", "last_30_days", "last_90_days"):
        days = int(key.split("_")[1])
        start = ref - timedelta(days=days - 1)
        return Period(key, f"Last {days} days ({start:%b %d} - {ref:%b %d, %Y})", start, ref)
    if key == "this_year":
        return Period(key, f"{ref.year} year to date", date(ref.year, 1, 1), ref)
    if key == "last_year":
        return Period(key, str(ref.year - 1), date(ref.year - 1, 1, 1), date(ref.year - 1, 12, 31))
    raise ToolError(f"Unknown period {period!r}. {PERIOD_HELP}")
