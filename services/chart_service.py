"""Plotly charts styled for the dark dashboard."""
from typing import List

import plotly.graph_objects as go

COPPER = "#D99A4E"
COPPER_SOFT = "#7A5A33"
STEEL = "#6C9BD2"
GRID = "#263244"
PALETTE = ["#D99A4E", "#6C9BD2", "#5CC59A", "#B58AE0", "#E8707A", "#8C99AB", "#E3C766"]


def _style(fig: go.Figure, height: int) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=24, b=8),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Manrope, Segoe UI, sans-serif", color="#C9D2DE", size=12),
        hoverlabel=dict(bgcolor="#1C2533", font_color="#E6EAF0"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    return fig


def monthly_revenue_fig(months: List[dict]) -> go.Figure:
    """Bar chart of revenue per month (an incomplete month is drawn in a softer colour)."""
    x = [m["month"] for m in months]
    y = [m["revenue"] for m in months]
    colors = [COPPER_SOFT if m.get("partial") else COPPER for m in months]
    fig = go.Figure(go.Bar(x=x, y=y, marker_color=colors,
                           hovertemplate="%{x}<br>Revenue: $%{y:,.0f}<extra></extra>"))
    fig.update_xaxes(type="category", showgrid=False)
    fig.update_yaxes(tickprefix="$", gridcolor=GRID, zeroline=False)
    return _style(fig, 330)


def top_products_fig(products: List[dict]) -> go.Figure:
    names = [p["product_name"] for p in products][::-1]
    values = [p["revenue"] for p in products][::-1]
    fig = go.Figure(go.Bar(x=values, y=names, orientation="h", marker_color=STEEL,
                           hovertemplate="%{y}<br>$%{x:,.0f}<extra></extra>"))
    fig.update_xaxes(tickprefix="$", gridcolor=GRID)
    fig.update_yaxes(showgrid=False)
    return _style(fig, 330)


def category_donut_fig(categories: List[dict]) -> go.Figure:
    fig = go.Figure(go.Pie(labels=[c["category"] for c in categories], values=[c["revenue"] for c in categories],
                           hole=0.62, marker=dict(colors=PALETTE, line=dict(color="#0E131B", width=2)),
                           textinfo="percent", sort=False,
                           hovertemplate="%{label}<br>$%{value:,.0f} (%{percent})<extra></extra>"))
    fig.update_layout(showlegend=True, legend=dict(orientation="v", x=1.0, y=0.5))
    return _style(fig, 330)
