"""
Weekly QA agent entry point.

For each site: render the page, run all checks, collect findings.
Then: write one Notion report page for the week, and post a per-site
Slack message only to channels whose site had findings.

Run manually with:  python src/main.py
Run in CI via:       .github/workflows/weekly-scan.yml
"""

from datetime import date

from config import SITES
from browser import fetch_rendered
from checks import (
    check_register_links,
    check_broken_links,
    check_images,
    check_date_consistency,
    check_countdown_present,
)
from report_builder import build_notion_report_markdown, build_slack_summary
from notion_client import create_audit_report_page
from slack_client import post_message


def scan_site(site: dict) -> dict:
    """Runs all checks for one site and returns its findings, grouped."""
    result = {"site": site["name"], "url": site["url"], "findings": [], "error": None}

    try:
        snapshot = fetch_rendered(site["url"])
    except Exception as e:
        result["error"] = f"{e.__class__.__name__}: {e}"
        return result

    findings = []
    findings += check_register_links(snapshot, site["platform"])
    findings += check_broken_links(snapshot)
    findings += check_images(snapshot)
    findings += check_date_consistency(snapshot)
    findings += check_countdown_present(snapshot)

    # Optional second page: conversion landing page, if the site has one.
    if site.get("landing_page_url"):
        try:
            landing_snapshot = fetch_rendered(site["landing_page_url"])
            findings += check_register_links(landing_snapshot, site["platform"])
            findings += check_broken_links(landing_snapshot)
            findings += check_images(landing_snapshot)
        except Exception as e:
            findings.append({
                "category": "Conversion Landing Page",
                "severity": "warning",
                "issue": f"Landing page failed to load: {e}",
                "checklist_item": "Conversion landing page is reachable",
            })

    result["findings"] = findings
    return result


def main():
    all_results = []
    for site in SITES:
        if site["platform"] == "unknown" and "robots.txt" in site.get("notes", ""):
            # Known-blocked site — skip the fetch, log it explicitly.
            all_results.append({
                "site": site["name"],
                "url": site["url"],
                "findings": [],
                "error": "Skipped: known to block automated access (robots.txt).",
            })
            continue
        all_results.append(scan_site(site))

    today = date.today().isoformat()
    report_title = f"Audit Report — Week of {date.today().strftime('%B %d, %Y')}"
    markdown_sections = build_notion_report_markdown(SITES, all_results)

    create_audit_report_page(
        title=report_title,
        date_iso=today,
        status="Complete",
        markdown_sections=markdown_sections,
    )

    # Slack: one message per site that actually has findings.
    for site, result in zip(SITES, all_results):
        summary = build_slack_summary(site, result, report_title)
        if summary:
            post_message(site["slack_channel"], summary)


if __name__ == "__main__":
    main()
