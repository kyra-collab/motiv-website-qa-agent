"""
Site configuration for the Motiv NA Website QA Agent.

platform: best-known default registration platform for this site.
    "letsdothis" | "active" | "mixed" | "unknown"
    "mixed" means different distances on the same site use different
    platforms — the scanner should detect per-button, not assume one.
notes: known quirks worth remembering when interpreting scan results.
"""

SITES = [
    {
        "name": "Surf City Marathon",
        "url": "https://www.runsurfcity.com/",
        "slack_channel": "#surfcitymarathon",
        "platform": "mixed",
        "notes": "Hero button -> Let's Do This, nav 'REGISTER' -> Active.com. Confirm intended platform.",
    },
    {
        "name": "Shamrock Run",
        "url": "https://www.shamrockrun.com/",
        "slack_channel": "#shamrock",
        "platform": "unknown",
        "notes": "Site blocks automated access (robots.txt). Needs manual check or allowlisted scraping approach.",
    },
    {
        "name": "Love Run Philly",
        "url": "https://www.loverunphilly.com/",
        "slack_channel": "#loverun",
        "platform": "letsdothis",
        "notes": "Clean, single platform.",
    },
    {
        "name": "Santa Barbara Wine Country Half",
        "url": "https://www.santabarbarawinehalf.com/",
        "slack_channel": "#santa-barbara",
        "platform": "letsdothis",
        "notes": "Has shown mismatched years across sections in the past — watch date consistency.",
    },
    {
        "name": "Bay to Breakers",
        "url": "https://www.baytobreakers.com/",
        "slack_channel": "#b2b",
        "platform": "active",
        "notes": "No direct register link reliably captured by simple fetch — needs headless browser check.",
    },
    {
        "name": "Napa to Sonoma",
        "url": "https://www.runnapatosonoma.com/",
        "slack_channel": "#n2s",
        "platform": "letsdothis",
        "notes": "Frequently sells out — 'waitlist' state is valid, not an error.",
    },
    {
        "name": "Surf City 10",
        "url": "https://www.surfcity10.com/",
        "slack_channel": "#sc10",
        "platform": "active",
        "notes": "All register buttons go to Active.com, not LDT. Has a /2026 conversion landing page too.",
        "landing_page_url": "https://www.surfcity10.com/2026",
    },
    {
        "name": "Long Beach Marathon",
        "url": "https://www.runlongbeach.com/",
        "slack_channel": "#lbm",
        "platform": "unknown",
        "notes": "CRITICAL HISTORY: has shown severely stale (2017-era) content. Verify freshness every run.",
    },
    {
        "name": "Santa Cruz Marathon",
        "url": "https://www.runsantacruz.com/",
        "slack_channel": "#santa-cruz",
        "platform": "letsdothis",
        "notes": "5K register button has pointed to the half-marathon page before — check distance-specific links carefully.",
    },
    {
        "name": "Golden Gate Half",
        "url": "https://www.goldengatehalf.com/",
        "slack_channel": "#golden-gate-half",
        "platform": "active",
        "notes": "Has shown stale prior-year event content/dates. Verify freshness every run.",
    },
    {
        "name": "Savannah Southern Half",
        "url": "https://www.southernhalf.com/",
        "slack_channel": "#savannah",
        "platform": "letsdothis",
        "notes": "Watch for year mismatches in medal/merch copy.",
    },
    {
        "name": "Run Malibu",
        "url": "https://www.runmalibu.com/",
        "slack_channel": "#runmalibu",
        "platform": "mixed",
        "notes": "Half Marathon & Combo -> Active.com. CSU Dolphin 5K -> Let's Do This. Per-distance, not per-site.",
    },
    {
        "name": "Golden State Challenge",
        "url": "https://www.goldenstatechallenge.com/",
        "slack_channel": "#gsc",
        "platform": "n/a",
        "notes": "Hub/index page only, links out to the other 12 sites. No pricing/registration content of its own.",
    },
]

NOTION_AUDIT_DATABASE_URL = "https://app.notion.com/p/augmentagency/39f1005fa41380099297db9d72e25b0e"
