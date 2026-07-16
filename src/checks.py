"""
Individual checks, each mapped to a line item on the Website Checklist
(Notion: "Website Checklist"). Each check returns a list of Finding
objects — empty list means "no issues found" for that check.

Some checks (register-link platform, date consistency) are heuristic:
they flag things worth a human look rather than asserting certainty.
Treat their output as "needs review," not as ground truth.
"""

from __future__ import annotations
from dataclasses import dataclass
import re
import requests

from browser import PageSnapshot

SKIP_LINK_SCHEMES = ("mailto:", "tel:", "javascript:")


@dataclass
class Finding:
    category: str          # e.g. "Pricing & Registration"
    severity: str          # "critical" | "warning" | "note"
    issue: str
    checklist_item: str


def check_register_links(snapshot: PageSnapshot, expected_platform: str) -> list[Finding]:
    findings = []
    register_links = [
        l for l in snapshot.links
        if "register" in l["text"].lower() or "sign up" in l["text"].lower()
    ]

    if not register_links:
        findings.append(Finding(
            category="Pricing & Registration",
            severity="warning",
            issue="No 'Register Now' style link found on the page.",
            checklist_item="Register Now button(s) link to correct registration platform",
        ))
        return findings

    platforms_seen = set()
    for link in register_links:
        href = link["href"].lower()
        if "letsdothis.com" in href:
            platforms_seen.add("letsdothis")
        elif "active.com" in href:
            platforms_seen.add("active")
        else:
            platforms_seen.add("other")

    if expected_platform == "mixed":
        # Multiple platforms are expected here; just record what we saw.
        return findings

    if len(platforms_seen) > 1:
        findings.append(Finding(
            category="Pricing & Registration",
            severity="warning",
            issue=f"Register buttons point to multiple platforms on one page: {sorted(platforms_seen)}.",
            checklist_item="Register Now button(s) link to correct registration platform",
        ))
    elif expected_platform not in ("unknown", "n/a") and expected_platform not in platforms_seen:
        findings.append(Finding(
            category="Pricing & Registration",
            severity="warning",
            issue=f"Expected platform '{expected_platform}' but found {sorted(platforms_seen)}.",
            checklist_item="Register Now button(s) link to correct registration platform",
        ))

    return findings


def check_broken_links(snapshot: PageSnapshot, timeout: int = 8) -> list[Finding]:
    findings = []
    checked = set()

    for link in snapshot.links:
        href = link["href"]
        if not href or href.startswith(SKIP_LINK_SCHEMES) or href in checked:
            continue
        checked.add(href)

        try:
            resp = requests.head(href, timeout=timeout, allow_redirects=True)
            if resp.status_code >= 400:
                # Some servers don't support HEAD properly; retry with GET.
                resp = requests.get(href, timeout=timeout, allow_redirects=True)
            if resp.status_code >= 400:
                findings.append(Finding(
                    category="Technical",
                    severity="critical" if resp.status_code == 404 else "warning",
                    issue=f"Link returns {resp.status_code}: {href}",
                    checklist_item="All internal/external links working (no 404s)",
                ))
        except requests.RequestException as e:
            findings.append(Finding(
                category="Technical",
                severity="warning",
                issue=f"Link failed to resolve ({e.__class__.__name__}): {href}",
                checklist_item="All internal/external links working (no 404s)",
            ))

    return findings


def check_images(snapshot: PageSnapshot) -> list[Finding]:
    findings = []
    for img in snapshot.images:
        if not img.get("loaded"):
            findings.append(Finding(
                category="Technical",
                severity="warning",
                issue=f"Image failed to load: {img.get('src', '(no src)')}",
                checklist_item="All images loading (no broken/missing images)",
            ))
    return findings


def check_date_consistency(snapshot: PageSnapshot) -> list[Finding]:
    """
    Heuristic: pull all 4-digit years mentioned near date-ish context and
    flag if more than 2 distinct years appear (some legitimate copy, e.g.
    '© 2026', mixes with race-date years — this needs a human look, not
    an auto-fail).
    """
    years = re.findall(r"\b(20[2-3]\d)\b", snapshot.text_content)
    distinct = set(years)
    if len(distinct) >= 3:
        return [Finding(
            category="Content Accuracy",
            severity="note",
            issue=f"Page mentions {len(distinct)} different years ({sorted(distinct)}) — verify all race-date references are current and consistent.",
            checklist_item="Event date and location are correct",
        )]
    return []


def check_countdown_present(snapshot: PageSnapshot) -> list[Finding]:
    """
    Confirms a countdown-timer-shaped element exists in the rendered text
    (e.g. 'd', 'h', 'm', 's' units near each other). This does NOT confirm
    it is counting down correctly — that needs a second fetch a few
    seconds apart to compare values, which the caller can add later.
    """
    if not re.search(r"\d+\s*d.{0,20}\d+\s*h.{0,20}\d+\s*m", snapshot.text_content, re.IGNORECASE | re.DOTALL):
        return [Finding(
            category="Pricing & Registration",
            severity="note",
            issue="No countdown-timer-shaped text found on the page — confirm one exists and is running.",
            checklist_item="Countdown timer is running and counting down to correct price increase",
        )]
    return []
