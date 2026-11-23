# Project Report - MCP-Powered AI Assistant

## 1. Purpose
A portfolio project showing how an AI application can **discover and use external tools through the Model Context Protocol
(MCP)** to analyse business data and produce reports. Target: AI Engineer internship / fresher applications.

## 2. Architecture

| Layer | Modules | Responsibility |
|---|---|---|
| Presentation | `app.py`, `ui/`, `assets/style.css` | Streamlit pages, dark theme, chat, downloads |
| Orchestration | `services/assistant.py` | Chooses Claude mode or demo mode, runs the tools, formats the answer |
| Planning | `services/claude_client.py`, `services/intent_router.py` | Claude tool-use loop / offline keyword planner |
| Tool execution | `services/tool_executor.py`, `services/mcp_client.py` | Direct calls or MCP stdio, history, error capture |
| Tools (MCP) | `mcp_servers/` | 24 tools, registry with JSON schemas, FastMCP server |
| Domain logic | `services/analytics.py`, `services/report_service.py` | Pandas calculations, insights, PDF/CSV |
| Data | `database/` | Schema, seed data, read-only query layer (SQLite / PostgreSQL) |
| Integrations | `integrations/` | PostgreSQL, CRM, Google Sheets, Slack (live or mock) |
| Cross-cutting | `config/`, `utils/` | Settings, validation, dates, logging |

**Key design decisions**

1. *One tool definition, two ways to run it.* `@registry.tool` builds name, description and JSON schema from a normal function.
   The same function is run in-process ("direct") or exposed through FastMCP ("mcp").
2. *Demo mode is a first-class feature.* The project must work with no paid API, so a transparent planner scores tools by
   keywords and fills arguments from the tool schemas.
3. *Honest integrations.* Every adapter reports `live`, `mock` or `not configured`; mock adapters write local files and say so.
4. *Relative dates use the latest sale date* so "last month" is meaningful with static demo data.
5. *Portable SQL.* Queries are plain SELECTs with `?` placeholders; aggregation happens in pandas, so SQLite and PostgreSQL
   behave the same.

## 3. Data model

* `products` (22 rows): id, name, category, unit_price, cost, stock
* `customers` (60 rows): id, name, email, phone, city, country, region, segment, joined_date
* `sales` (1,577 rows, 12 months): id, sale_date, customer_id, product_id, quantity, unit_price, discount_pct, total_amount,
  payment_method, channel

Generated with seed 42 and built-in patterns: seasonality (Nov/Dec peak), growth over the year, a rising product
(Nova Max Pro), a declining product (TabMini 8), low-stock best sellers, and customer concentration - so the insights have
something real to find. An order is one sales row, so average order value = revenue / rows.

## 4. Tool catalogue (24)

| # | Tool | Purpose |
|---|---|---|
| 1 | `get_all_sales` | Paged sales records |
| 2 | `get_sales_by_date_range` | Sales between two dates |
| 3 | `calculate_total_revenue` | Revenue, profit, orders, units |
| 4 | `calculate_monthly_sales` | Monthly revenue, orders, growth |
| 5 | `find_best_selling_products` | Rank by revenue / units / profit |
| 6 | `find_worst_selling_products` | Weakest products (includes zero-sales) |
| 7 | `analyze_product_performance` | One product: rank, margin, trend, verdict |
| 8 | `calculate_average_order_value` | AOV, median, largest order |
| 9 | `identify_low_performing_products` | Products far below average revenue |
| 10 | `generate_sales_summary` | Totals, top product/category/customer, regions, change vs previous |
| 11 | `export_sales_report` | Detailed sales rows to CSV |
| 12 | `search_customers` | Search by name/email/city/region/segment |
| 13 | `get_customer_details` | Profile, lifetime value, recent purchases |
| 14 | `create_business_insights` | Rule-based insights + recommendations |
| 15 | `generate_report` | PDF or CSV business report |
| 16 | `compare_periods` | Period vs period, incl. like-for-like |
| 17 | `get_revenue_by_category` | Category breakdown |
| 18 | `get_top_customers` | Highest-revenue customers |
| 19 | `list_products` | Catalogue and stock |
| 20 | `get_data_overview` | Table sizes, date range |
| 21 | `get_integration_status` | LIVE / MOCK status of integrations |
| 22 | `send_report_to_slack` | Slack summary (mock unless webhook set) |
| 23 | `sync_sales_to_google_sheets` | Monthly table to Sheets (mock unless configured) |
| 24 | `get_crm_contact` | CRM record by email (sample file unless configured) |

## 5. Security measures

* Secrets only from environment / `.env`; `.env` git-ignored; key masked in any status text; never logged.
* Database access is `SELECT`/`WITH` only, with bound parameters (`PRAGMA query_only` on SQLite).
* The AI can call only registered tools; unknown names and unknown arguments are rejected; argument types are coerced and checked.
* Range / format validation for dates, integers, choices, e-mails, text length (500-character question limit).
* Report files: allowed extensions `.pdf`/`.csv`, restricted character set, resolved path must stay inside `reports/`.
* Slack webhook must be on `hooks.slack.com`; CRM must be `https`.
* Tool errors never crash the app; they are returned as structured errors and logged to `logs/app.log`.
* Tool-use loop capped at 6 rounds; tool output sent to Claude is size-limited.

## 6. Testing and verification results

**Automated tests - 44 tests, all passing** (`python -m unittest discover -s tests -t . -v`):

| File | Tests | Covers |
|---|---|---|
| `test_database.py` | 7 | connection, table sizes, reference date, joins, date filter, SELECT-only rule, CSV export of sample data |
| `test_validators.py` | 6 | dates, ints, text, choices, e-mail, safe report paths, period maths |
| `test_tools.py` | 17 | all 24 tools executed; known values (Oct 2026 revenue $48,497.15, 168 orders); PDF/CSV validity; bad input rejection; mock labelling |
| `test_assistant.py` | 8 | the seven sample questions, the example from the brief (PDF created), parameter extraction, help/unknown input, history |
| `test_integrations.py` | 6 | adapters in mock mode, Slack host check, demo-mode switch, key masking, Claude agent loop with a fake API |

**Other checks performed**

* All 24 tools executed against the real sample database, including 7 deliberate bad-input cases.
* PDF report rendered to an image and inspected (KPIs, insights, tables, bar chart, footer).
* Every Streamlit page was executed end to end (dashboard, chat with two real questions, reports, tools, integrations,
  including the "Generate report" and "Run tool" buttons) using stand-in `streamlit`/`plotly` modules.

**What was NOT verified in the build environment** (no internet, so these packages could not be installed there):
the real Streamlit browser rendering, real Plotly drawing, the real `mcp` package (FastMCP server + stdio client), and live
Claude API calls. That code follows the documented APIs of those libraries, and the Claude loop is tested with a fake
client, but you should do a first run on your own machine - see README section 14 if anything misbehaves.

## 7. Limitations
See README section 12. Main points: demo-mode language understanding is limited by design; MCP mode starts a process per
request; live PostgreSQL/Sheets/CRM/Slack paths need your credentials and were not run here.

## 8. Future work
Persistent MCP session, authentication and roles, streaming answers, forecasting, scheduled e-mail reports, more connectors,
Docker, CI pipeline.
