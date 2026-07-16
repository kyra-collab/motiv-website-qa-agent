"""
Turns raw per-site Finding lists into:
  1. The per-site markdown sections used in the Notion Audit Report
     (same structure as the manually-created template).
  2. A short Slack message per site, only generated when there's
     something to report.
"""

SEVERITY_EMOJI = {"critical": "🔴", "warning": "🟡", "note": "⚪"}
CATEGORIES = ["Pricing & Registration", "Content Accuracy", "Technical", "Miscellaneous", "Conversion Landing Page"]


def _site_status_emoji(findings, error) -> str:
    if error:
        return "⚪"
    if any(f.severity == "critical" for f in findings):
        return "🔴"
    if any(f.severity == "warning" for f in findings):
        return "🟡"
    return "🟢"


def build_notion_report_markdown(sites: list[dict], results: list[dict]) -> list[str]:
    sections = []

    scanned = sum(1 for r in results if not r["error"])
    critical_sites = sum(1 for r in results if any(f.severity == "critical" for f in r["findings"]))
    clean_sites = sum(1 for r in results if not r["error"] and not r["findings"])

    summary = (
        f"## Summary\n\n"
        f"- Sites scanned: {scanned} / {len(sites)}\n"
        f"- Sites with critical issues: {critical_sites}\n"
        f"- Sites clean: {clean_sites}\n"
    )
    sections.append(summary)

    for site, result in zip(sites, results):
        status_emoji = _site_status_emoji(result["findings"], result["error"])
        block = [f"## {site['name']} — {site['slack_channel']}", f"**Status:** {status_emoji}", ""]

        if result["error"]:
            block.append(f"**Not scanned:** {result['error']}")
            sections.append("\n".join(block))
            continue

        by_category = {c: [] for c in CATEGORIES}
        for f in result["findings"]:
            by_category.setdefault(f.category, []).append(f)

        for category in CATEGORIES:
            findings = by_category.get(category, [])
            block.append(f"**{category}**")
            if findings:
                for f in findings:
                    block.append(f"- {SEVERITY_EMOJI[f.severity]} {f.issue}")
            else:
                block.append("- No issues found")
            block.append("")

        sections.append("\n".join(block))

    return sections


def build_slack_summary(site: dict, result: dict, report_title: str) -> str | None:
    """Returns None if there's nothing worth pinging the channel about."""
    if result["error"]:
        return None
    if not result["findings"]:
        return None

    critical = [f for f in result["findings"] if f.severity == "critical"]
    warnings = [f for f in result["findings"] if f.severity == "warning"]

    lines = [f"*Website QA — {site['name']}*"]
    if critical:
        lines.append(f":red_circle: {len(critical)} critical issue(s):")
        lines += [f"  • {f.issue}" for f in critical]
    if warnings:
        lines.append(f":large_yellow_circle: {len(warnings)} warning(s):")
        lines += [f"  • {f.issue}" for f in warnings]
    lines.append(f"Full report: {report_title} (Notion)")

    return "\n".join(lines)
