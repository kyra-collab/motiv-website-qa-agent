"""
Minimal Notion API client — creates a new page in the Audit Report
database each week and writes the per-site findings into its body.
Uses the raw REST API directly (no SDK dependency) so it's easy to
audit what's being sent.

Requires env vars:
    NOTION_API_KEY       - internal integration token, shared with the
                            "Audit Report" database in Notion
    NOTION_AUDIT_DB_ID    - the data source / database ID (not the URL)
"""

import os
import re
import time
import requests

NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"

# Notion's API caps children-block writes at 100 blocks per request.
BLOCK_BATCH_SIZE = 100
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3


def _headers() -> dict:
    api_key = os.environ["NOTION_API_KEY"]
    return {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _request_with_retry(method: str, url: str, **kwargs) -> requests.Response:
    """
    Notion's API can be slow when writing a lot of blocks. Retries on
    timeouts and 5xx errors with a short backoff before giving up.
    """
    kwargs.setdefault("timeout", REQUEST_TIMEOUT)
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.request(method, url, **kwargs)
            if resp.status_code >= 500:
                last_error = f"Notion returned {resp.status_code}: {resp.text[:200]}"
            else:
                resp.raise_for_status()
                return resp
        except requests.exceptions.Timeout:
            last_error = "Request timed out"
        except requests.exceptions.RequestException as e:
            last_error = str(e)

        if attempt < MAX_RETRIES:
            time.sleep(2 * attempt)  # 2s, then 4s

    raise RuntimeError(f"Notion API call failed after {MAX_RETRIES} attempts: {last_error}")


def _parse_inline(text: str) -> list[dict]:
    """
    Splits a line on '**bold**' markers and returns Notion rich_text
    segments with bold annotation applied where appropriate. Anything
    else (links, italics, etc.) is treated as plain text — the report
    builder doesn't currently emit those, so this covers what we need.
    """
    segments = []
    parts = re.split(r"(\*\*.*?\*\*)", text)
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            content = part[2:-2]
            segments.append({
                "type": "text",
                "text": {"content": content},
                "annotations": {"bold": True},
            })
        else:
            segments.append({"type": "text", "text": {"content": part}})
    return segments or [{"type": "text", "text": {"content": ""}}]


def markdown_to_blocks(markdown: str) -> list[dict]:
    """
    Converts the specific markdown subset produced by report_builder.py
    (##, **bold**, "- " bullets, "---" dividers, plain paragraphs) into
    Notion block objects. Not a general-purpose markdown parser —
    intentionally scoped to what the report actually emits.
    """
    blocks = []
    for raw_line in markdown.split("\n"):
        line = raw_line.rstrip()

        if not line:
            continue
        if line.strip() == "---":
            blocks.append({"object": "block", "type": "divider", "divider": {}})
        elif line.startswith("## "):
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": _parse_inline(line[3:])},
            })
        elif line.startswith("- "):
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": _parse_inline(line[2:])},
            })
        else:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": _parse_inline(line)},
            })
    return blocks


def _append_blocks_in_batches(page_id: str, blocks: list[dict]) -> None:
    for i in range(0, len(blocks), BLOCK_BATCH_SIZE):
        batch = blocks[i:i + BLOCK_BATCH_SIZE]
        _request_with_retry(
            "PATCH",
            f"{BASE_URL}/blocks/{page_id}/children",
            headers=_headers(),
            json={"children": batch},
        )


def create_audit_report_page(title: str, date_iso: str, status: str, markdown_sections: list[str]) -> str:
    """
    Creates a page in the Audit Report database with its properties set,
    then appends the per-site findings as page content, converted from
    the markdown report_builder.py produces.
    """
    db_id = os.environ["NOTION_AUDIT_DB_ID"]

    payload = {
        "parent": {"data_source_id": db_id},
        "properties": {
            "Report": {"title": [{"text": {"content": title}}]},
            "Date": {"date": {"start": date_iso}},
            "Status": {"status": {"name": status}},
        },
    }

    resp = _request_with_retry("POST", f"{BASE_URL}/pages", headers=_headers(), json=payload)
    page_id = resp.json()["id"]

    full_markdown = "\n\n".join(markdown_sections)
    blocks = markdown_to_blocks(full_markdown)
    if blocks:
        _append_blocks_in_batches(page_id, blocks)

    return page_id
