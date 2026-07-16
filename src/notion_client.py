"""
Minimal Notion API client — just enough to create a new page in the
Audit Report database each week. Uses the raw REST API directly
(no SDK dependency) so it's easy to audit what's being sent.

Requires env vars:
    NOTION_API_KEY       - internal integration token, shared with the
                            "Audit Report" database in Notion
    NOTION_AUDIT_DB_ID    - the data source / database ID (not the URL)
"""

import os
import requests

NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"


def _headers() -> dict:
    api_key = os.environ["NOTION_API_KEY"]
    return {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def create_audit_report_page(title: str, date_iso: str, status: str, markdown_sections: list[str]) -> str:
    """
    Creates a page in the Audit Report database.

    markdown_sections: list of per-site markdown blocks (already formatted
    the way the report template expects — see report_builder.py). Notion's
    REST API doesn't take raw markdown for content blocks directly, so in
    practice this should be swapped for the Notion MCP tools (as used in
    the exploratory phase of this project) OR expanded here to convert
    markdown into the API's block-object format. Left as the integration
    point since block-conversion is mechanical but verbose.
    """
    db_id = os.environ["NOTION_AUDIT_DB_ID"]

    payload = {
        "parent": {"data_source_id": db_id},
        "properties": {
            "Report": {"title": [{"text": {"content": title}}]},
            "Date": {"date": {"start": date_iso}},
            "Status": {"status": {"name": status}},
        },
        # NOTE: children blocks omitted here — see docstring above.
        # Simplest path: call this to create the page + properties, then
        # use notion-update-page (insert_content) with the markdown body,
        # same as done manually earlier in this project.
    }

    resp = requests.post(f"{BASE_URL}/pages", headers=_headers(), json=payload, timeout=15)
    resp.raise_for_status()
    return resp.json()["id"]
