# Motiv NA Website QA Agent

Weekly automated scan of the 13 Motiv NA portfolio websites against the
[Website Checklist](https://app.notion.com/p/augmentagency/Website-Checklist-39d1005fa41380358c53c89e5e3ca37a).
Results are written to the [Audit Report database](https://app.notion.com/p/augmentagency/39f1005fa41380099297db9d72e25b0e)
in Notion, and posted to each site's Slack channel when there's something
to flag.

## What's implemented

- Headless-browser page rendering (Playwright) — needed because pricing,
  countdown timers, and register links are JS-rendered on Wix.
- Checks: register-link platform mismatch, broken links (internal +
  external), broken images, date-consistency heuristic, countdown-timer
  presence.
- Slack posting per site (only when there are findings).
- GitHub Actions workflow, scheduled weekly, with manual trigger option.

## What's NOT implemented yet — do this before relying on it

1. **Let's Do This / Active.com price comparison.** This needs per-platform
   scraping logic (their DOM structures differ, and pricing may sit behind
   a "select your race" step). Not built — `checks.py` has no price-match
   function yet. This is the most complex remaining piece.
2. **Trend Tracker (Google Sheets) phase check.** `gspread` is in
   `requirements.txt` but there's no code reading the sheet yet — needs a
   Google service account with read access to the sheet, and a mapping of
   sheet rows to site name.
3. **Notion page body writing.** `notion_client.py` creates the report
   page and its properties, but does not yet attach the per-site markdown
   as page content — the Notion API needs markdown converted into its
   block-object format first. Fastest path: reuse the Notion MCP tools
   (as used earlier in this project) instead of the raw REST call, if
   this ever runs somewhere those tools are available; otherwise, extend
   `notion_client.py` with a markdown-to-blocks converter.
4. **`shamrockrun.com`** blocks automated access outright (robots.txt).
   `main.py` currently just logs it as skipped — needs a manual-check
   process or a decision to scrape anyway (raises a ToS question, flagged
   for Kyra to weigh in on, not a default the code should assume).
5. **`baytobreakers.com`** register link wasn't reliably captured even
   with a headless browser in initial testing — worth a manual look at
   why (may need a longer wait condition, or the button may be JS-injected
   later than the others).

## Setup

1. Create secrets in the GitHub repo (Settings → Secrets and variables →
   Actions):
   - `NOTION_API_KEY` — internal integration token, shared with the Audit
     Report database in Notion (Notion → database → "..." → Connections)
   - `NOTION_AUDIT_DB_ID` — the database ID from its URL
   - `SLACK_BOT_TOKEN` — bot token with `chat:write`, invited into every
     channel listed in `src/config.py`
2. Push this repo to GitHub. The workflow runs automatically every Monday
   09:00 UTC, or trigger it manually from the Actions tab
   ("Run workflow").
3. To test locally first:
   ```bash
   pip install -r requirements.txt
   playwright install --with-deps chromium
   cp .env.example .env   # fill in the three values
   python src/main.py
   ```

## Project layout

```
src/
  config.py          # the 13 sites, their Slack channels, known quirks
  browser.py          # Playwright wrapper — renders a page, extracts links/images/text
  checks.py            # one function per checklist item
  report_builder.py   # turns findings into Notion markdown + Slack text
  notion_client.py     # posts the weekly report page
  slack_client.py      # posts per-site Slack messages
  main.py              # orchestrates all of the above
.github/workflows/
  weekly-scan.yml      # the cron schedule
```
