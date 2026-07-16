"""
Headless-browser helpers.

Wix pages (countdown timers, dynamic pricing) render via JS, so we need a
real browser rather than a plain HTTP fetch. This module centralizes
Playwright usage so the rest of the codebase doesn't touch it directly.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from playwright.sync_api import sync_playwright


@dataclass
class PageSnapshot:
    url: str
    html: str
    links: list[dict] = field(default_factory=list)   # [{text, href}]
    images: list[dict] = field(default_factory=list)   # [{src, alt, loaded}]
    text_content: str = ""
    load_errors: list[str] = field(default_factory=list)


def fetch_rendered(url: str, timeout_ms: int = 20000) -> PageSnapshot:
    """
    Load a URL in a headless browser and return a structured snapshot:
    all links, all images (with a best-effort loaded check), visible
    text, and any network/console errors encountered.
    """
    load_errors: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        page.on("console", lambda msg: load_errors.append(f"console:{msg.type}:{msg.text}")
                if msg.type == "error" else None)
        page.on("requestfailed", lambda req: load_errors.append(f"requestfailed:{req.url}"))

        page.goto(url, timeout=timeout_ms, wait_until="networkidle")

        html = page.content()
        text_content = page.inner_text("body")

        links = page.eval_on_selector_all(
            "a[href]",
            "els => els.map(e => ({text: e.innerText.trim(), href: e.href}))",
        )

        images = page.eval_on_selector_all(
            "img",
            """els => els.map(e => ({
                src: e.src,
                alt: e.alt,
                loaded: e.complete && e.naturalWidth > 0
            }))""",
        )

        browser.close()

    return PageSnapshot(
        url=url,
        html=html,
        links=links,
        images=images,
        text_content=text_content,
        load_errors=load_errors,
    )
