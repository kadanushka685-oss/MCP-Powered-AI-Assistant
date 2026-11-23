"""Formatting helpers shared by the tools, reports and UI."""
import json
from typing import Optional

import pandas as pd

from config import settings


def money(value: Optional[float], decimals: int = 2) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "n/a"
    return f"{settings.CURRENCY_SYMBOL}{value:,.{decimals}f}"


def compact_money(value: Optional[float]) -> str:
    """$1.2M / $34.5K style numbers for dashboard cards."""
    if value is None:
        return "n/a"
    sign = "-" if value < 0 else ""
    number = abs(float(value))
    if number >= 1_000_000:
        return f"{sign}{settings.CURRENCY_SYMBOL}{number / 1_000_000:.2f}M"
    if number >= 10_000:
        return f"{sign}{settings.CURRENCY_SYMBOL}{number / 1_000:.1f}K"
    return f"{sign}{settings.CURRENCY_SYMBOL}{number:,.0f}"


def pct(value: Optional[float], signed: bool = True) -> str:
    if value is None:
        return "n/a"
    return f"{value:+.1f}%" if signed else f"{value:.1f}%"


def df_to_records(df: pd.DataFrame) -> list:
    """DataFrame -> list of plain dicts that are safe to send as JSON."""
    if df is None or df.empty:
        return []
    return json.loads(df.to_json(orient="records", date_format="iso"))
