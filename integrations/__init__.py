"""Integration adapters (PostgreSQL, CRM, Google Sheets, Slack)."""
from integrations.crm_adapter import CRMAdapter
from integrations.postgres_adapter import PostgresAdapter
from integrations.sheets_adapter import GoogleSheetsAdapter
from integrations.slack_adapter import SlackAdapter


def get_integrations() -> dict:
    """Fresh adapter objects that read the current settings."""
    return {"postgres": PostgresAdapter(), "crm": CRMAdapter(),
            "sheets": GoogleSheetsAdapter(), "slack": SlackAdapter()}
