# MCP-Powered AI Assistant - Enterprise Tool Integration & Workflow Automation

An AI assistant that understands plain-English business questions, **discovers the tools it can use**, runs them
against a sales database, and returns analysis, charts and downloadable PDF/CSV reports in a dark enterprise dashboard.

> Example: *"Analyze last month's sales and create a detailed report."*
> The assistant discovers the tools, pulls the sales data, calculates the numbers, writes insights, builds a PDF and shows
> every tool it ran.

**It works without any paid API.** With no API key the project runs in **Demo mode** (a rule-based planner picks the tools).
Add a Claude API key and Claude plans the tool calls itself.

---

## 1. Features

- **24 working MCP tools** (sales, customers, insights, reports, integrations) served by a FastMCP server
- **Dynamic tool discovery** - the assistant asks for the tool list; it never has a hard-coded list
- **Two AI modes**: Demo mode (no key) and Claude mode (Anthropic tool use)
- **Dashboard**: revenue / sales / customers / AOV cards, monthly sales chart, category chart, best-selling products,
  recent sales, AI insights, PDF report button
- **AI chat** with a visible **tool trace** (which tool ran, with what arguments, how long it took)
- **Reports** as PDF (reportlab) or CSV, with downloads in the UI
- **Tool execution history** and a "Try a tool" console
- **Integration adapters** - PostgreSQL, CRM, Google Sheets, Slack. Real connections are optional; without credentials
  they run as **clearly labelled MOCKS** that never pretend data was sent anywhere
- **Security basics**: `.env` secrets, input validation, read-only SELECT-only database access, tool allow-list,
  sanitised report file names, error handling and logging
- **44 automated tests** and sample data included

## 2. Technology stack

| Area | Technology |
|---|---|
| Language | Python 3.10+ |
| Tool protocol | MCP (Model Context Protocol) with the official SDK's **FastMCP** |
| Frontend | Streamlit (dark theme + custom CSS) |
| Database | SQLite (default), PostgreSQL adapter (optional) |
| Analysis | Pandas |
| Charts | Plotly |
| AI | Anthropic Claude API (tool use) - optional |
| Reports | reportlab (PDF), csv |
| Config | python-dotenv |

## 3. Folder structure

```
MCP_AI_Assistant/
|-- app.py                  Streamlit entry point (sidebar + page routing)
|-- requirements.txt        Packages to install
|-- requirements-optional.txt  Extra packages for real integrations
|-- .env.example            Template for your settings / API key
|-- README.md  PROJECT_REPORT.md
|-- config/settings.py      All settings, read from environment variables
|-- database/
|   |-- schema.sql          Table definitions
|   |-- seed_data.py        Realistic sample-data generator (seed 42)
|   |-- init_db.py          Creates / resets the database
|   |-- connection.py       Read-only query helper (SQLite or PostgreSQL)
|   |-- repository.py       All SQL queries
|   `-- sales.db            Ready-made sample database
|-- mcp_servers/
|   |-- registry.py         Tool registry (discovery, schema, validation)
|   |-- sales_tools.py  customer_tools.py  report_tools.py  integration_tools.py   <- the 24 tools
|   `-- server.py           FastMCP server (stdio)
|-- services/
|   |-- assistant.py        Orchestrator: chooses Claude or demo mode
|   |-- intent_router.py    Demo-mode planner (tool scoring + argument extraction)
|   |-- claude_client.py    Claude tool-use loop
|   |-- mcp_client.py       Talks to the MCP server over stdio
|   |-- tool_executor.py    Runs tools (direct or via MCP) + execution history
|   |-- analytics.py        Pandas calculations + business insights
|   |-- report_service.py   PDF and CSV report builder
|   |-- response_formatter.py  Turns tool results into Markdown
|   `-- chart_service.py    Plotly charts
|-- integrations/           postgres / crm / sheets / slack adapters (live or mock)
|-- ui/                     Streamlit pages: dashboard, chat, reports, tools, integrations
|-- utils/                  validators, dates, formatting, logger
|-- assets/style.css        Dark theme styling
|-- reports/                Generated reports (a sample PDF is included)
|-- sample_data/            CSV copies of the sample data + sample CRM file
`-- tests/                  44 tests + sample questions and expected outputs
```

## 4. Installation on Windows (step by step)

You need **Python 3.10 or newer** (check with `python --version`; download from python.org and tick
*"Add Python to PATH"* during setup) and **VS Code**.

1. Unzip `MCP_AI_Assistant.zip`, for example to `C:\Projects\MCP_AI_Assistant`.
2. Open VS Code -> **File > Open Folder...** -> choose the `MCP_AI_Assistant` folder.
3. Install the VS Code extensions **Python** and **Pylance** (Extensions icon on the left).
4. Open the terminal: **Terminal > New Terminal** (PowerShell) and run:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell says *"running scripts is disabled"*, run this once and activate again:
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`
(or use Command Prompt and `.venv\Scripts\activate.bat`).

5. In VS Code press **Ctrl+Shift+P** -> *Python: Select Interpreter* -> choose the one inside `.venv`.

## 5. Run the project

```powershell
python -m streamlit run app.py
```

The browser opens at http://localhost:8501. The sample database is already included. To rebuild it around today's date
(so "last month" always has data):

```powershell
python -m database.init_db --reset
```

Other commands:

```powershell
python -m unittest discover -s tests -t . -v      # run all 44 tests
python -m tests.run_sample_queries                # print answers to the sample questions
python mcp_servers/server.py                      # start the MCP server on its own (stdio)
```

## 6. Configure API keys (all optional)

The **only file you edit** is `.env`:

1. In VS Code Explorer, right-click `.env.example` -> *Copy*, then *Paste*, and rename the copy to `.env`.
2. Open `.env` and set the line `ANTHROPIC_API_KEY=` to your key (no quotes, no spaces):
   `ANTHROPIC_API_KEY=sk-ant-...`
3. Restart Streamlit (`Ctrl+C`, then run it again).

The sidebar then shows *Claude (model)* instead of *Demo mode*. If the key or model name is wrong, the app shows a clear
message and **falls back to demo mode** for that answer. `CLAUDE_MODEL` can be changed in `.env` if you want another model.
Never commit `.env` (it is in `.gitignore`).

Real integrations (also optional, set in `.env`): `SLACK_WEBHOOK_URL`, `GOOGLE_SHEETS_CREDENTIALS_FILE` +
`GOOGLE_SHEETS_SPREADSHEET_ID` (`pip install gspread`), `CRM_BASE_URL` + `CRM_API_KEY`, and for PostgreSQL
`DB_BACKEND=postgres` + `DATABASE_URL` (`pip install psycopg2-binary`). The **Integrations** page always shows whether each
one is LIVE, MOCK or not configured.

## 7. How MCP works in this project

**MCP (Model Context Protocol)** is a standard way for an AI application (the *client*) to ask a *server* "which tools do you
offer?" and then call them. The tools describe themselves (name, description, JSON input schema), so the AI can choose
and use them without custom glue code for each tool.

```
 You ask a question
        |
        v
 [Streamlit chat] --> [SalesAssistant] --discover--> tool list (name, description, schema)
                            |
        Demo mode: keyword planner picks tools          Claude mode: Claude picks tools (tool use)
                            |
                            v
                    [ToolExecutor]  (validates the arguments, logs every call)
                       |                         |
          direct mode (default)         MCP mode (sidebar checkbox)
          registry.call(...)            MCPClient --stdio--> mcp_servers/server.py (FastMCP)
                       \\                         /
                        v                       v
                 the same 24 tool functions -> repository -> SQLite / PostgreSQL
                            |
                            v
              analytics + insights + PDF/CSV  -> answer, charts, downloads, tool trace
```

* `mcp_servers/registry.py` - each tool is a normal Python function with `@registry.tool(...)`. The registry builds the
  JSON schema from the type hints, so adding a tool = writing one function.
* `mcp_servers/server.py` - registers every tool with **FastMCP**, so any MCP client (this app, Claude Desktop,
  the MCP Inspector) can use them.
* **Direct mode** calls the same functions in-process (fast, default). **MCP mode** (sidebar checkbox *Use real MCP server*)
  starts `server.py` and goes through the real protocol. Both modes produce identical results.

### The 24 tools

| Group | Tools |
|---|---|
| Sales data | `get_all_sales`, `get_sales_by_date_range`, `get_data_overview`, `list_products` |
| Revenue and trends | `calculate_total_revenue`, `calculate_monthly_sales`, `calculate_average_order_value`, `compare_periods`, `get_revenue_by_category` |
| Products | `find_best_selling_products`, `find_worst_selling_products`, `analyze_product_performance`, `identify_low_performing_products` |
| Summary and insights | `generate_sales_summary`, `create_business_insights` |
| Customers | `search_customers`, `get_customer_details`, `get_top_customers` |
| Reports | `export_sales_report` (CSV rows), `generate_report` (PDF or CSV) |
| Integrations | `get_integration_status`, `send_report_to_slack`, `sync_sales_to_google_sheets`, `get_crm_contact` |

## 8. Sample questions

| Question | Tools used |
|---|---|
| Analyze last month's sales. | `generate_sales_summary`, `find_best_selling_products`, `create_business_insights` |
| Which product generated the highest revenue? | `find_best_selling_products` |
| Show monthly revenue. | `calculate_monthly_sales` |
| Find the top 5 selling products. | `find_best_selling_products` |
| Compare this month and last month. | `compare_periods` |
| Generate a PDF sales report. | `generate_report` |
| Give me business growth suggestions. | `create_business_insights` |

Full answers are in `tests/expected_outputs.md`. "Last month" means the month before the latest sale in the database.

## 9. Screenshots (for your portfolio / GitHub)

1. Run the app and make the browser window about 1400 px wide.
2. **Dashboard** page -> press `Win + Shift + S` -> drag over the browser -> save as `screenshots/dashboard.png`.
3. **AI Assistant** page -> click *Analyze last month's sales.* -> expand *Tool trace* -> capture `screenshots/chat.png`.
4. **Tools and history** -> *Execution history* tab -> capture `screenshots/history.png`.
5. **Integrations** page -> capture `screenshots/integrations.png`.
6. Add them to this README with `![Dashboard](screenshots/dashboard.png)`.

## 10. Testing

```powershell
python -m unittest discover -s tests -t . -v
```

44 tests cover the database connection, validators, all 24 tools, PDF/CSV reports, the seven sample questions, mock
integrations and the Claude tool-use loop (with a fake API, so no key or internet is needed). Tests use a temporary
database and never touch your real one.

## 11. Interview explanation

**30-second pitch.** "I built an AI assistant that connects to business tools through MCP. Tools are Python functions that
describe themselves, so the assistant discovers them at runtime, picks the right ones for a question like 'analyze last
month's sales', runs them, and returns a report. It works offline in demo mode and uses Claude's tool use when an API key
is present."

**Questions you should be ready for**

* *What is MCP and why use it?* A standard protocol for tools. The AI asks the server for a tool list and calls tools by
  name with JSON arguments, so I can add or change tools without changing the AI code.
* *How does tool discovery work?* `registry.describe()` (or MCP `list_tools`) returns name, description and JSON schema.
  The planner or Claude chooses from that list; nothing is hard-coded.
* *How does demo mode choose tools?* It scores each tool's keywords against the question, extracts values (period, top N,
  product, email) and fills the arguments from the tool's own schema. See `services/intent_router.py`.
* *How do you stop the AI making up numbers?* The system prompt forbids it, and every number comes from a tool that runs a
  database query. The UI shows the tool trace as proof.
* *How is it secure?* Secrets only in `.env`; read-only SELECT with bound parameters; the AI can only call registered tools;
  arguments are type-checked and range-checked; report files are restricted to `reports/` with sanitised names;
  Slack webhook host is checked; the API key is never shown or logged.
* *Why a registry plus FastMCP?* One function definition powers both the in-process mode and the real MCP server.
* *What would you improve?* See below.

## 12. Known limitations

* Demo mode understands the listed kinds of questions, not free-form language - that is what Claude mode is for.
* The MCP mode opens a new server process per request: simple and reliable, but slower than one persistent session.
* PostgreSQL, Google Sheets and live CRM/Slack adapters are written for the real services but are not covered by automated
  tests (they need credentials); mock mode is tested.
* Sample data is generated, not real.

## 13. Future improvements

User login and roles; persistent MCP session; streaming Claude answers; forecasting (time-series); scheduled reports by
email; more connectors (HubSpot, Salesforce, Stripe); Docker image; CI with GitHub Actions; caching with Redis;
dashboards per region/channel.

## 14. Troubleshooting

| Problem | Fix |
|---|---|
| `streamlit` is not recognised | Use `python -m streamlit run app.py` with the virtual environment activated |
| `ModuleNotFoundError` | Activate `.venv`, then `pip install -r requirements.txt` |
| "last month" shows no data | `python -m database.init_db --reset` |
| MCP checkbox shows an error | `pip install mcp`, then retry; otherwise leave the checkbox off (direct mode) |
| PDF says reportlab is missing | `pip install reportlab`, or choose CSV |
| Claude call failed | Check the key in `.env`, the `CLAUDE_MODEL` name and your internet; the app falls back to demo mode |
| Details of any error | Open `logs/app.log` |
