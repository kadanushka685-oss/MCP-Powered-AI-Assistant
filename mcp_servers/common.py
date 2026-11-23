"""Helpers shared by all tool modules."""
from datetime import date
from typing import Optional

import pandas as pd

from database import repository
from utils.dates import PERIOD_HELP, Period, resolve_period
from utils.validators import ToolError, validate_date

PERIOD_DOC = PERIOD_HELP
START_DOC = "Optional start date (YYYY-MM-DD). Overrides 'period' when given."
END_DOC = "Optional end date (YYYY-MM-DD). Overrides 'period' when given."


def resolve(period: Optional[str], start_date: Optional[str] = None,
            end_date: Optional[str] = None) -> Period:
    """Build a Period from either explicit dates or a period name."""
    if start_date or end_date:
        start = validate_date(start_date, "start_date") if start_date else None
        end = validate_date(end_date, "end_date") if end_date else None
        if start and end and start > end:
            raise ToolError("start_date must not be after end_date.")
        label = f"{start or 'beginning'} to {end or 'latest'}"
        return Period("custom", label, start, end)
    return resolve_period(period or "all", repository.get_reference_date())


def load_sales(period: Period) -> pd.DataFrame:
    return repository.get_sales_df(period.start, period.end)


def reference_date() -> date:
    return repository.get_reference_date()
