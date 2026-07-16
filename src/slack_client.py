"""
Minimal Slack API client — posts a single message to a channel.

Requires env var:
    SLACK_BOT_TOKEN  - bot token with chat:write scope, invited into
                       every channel listed in config.SITES
"""

import os
import requests

BASE_URL = "https://slack.com/api"


def post_message(channel: str, text: str) -> None:
    token = os.environ["SLACK_BOT_TOKEN"]
    resp = requests.post(
        f"{BASE_URL}/chat.postMessage",
        headers={"Authorization": f"Bearer {token}"},
        json={"channel": channel, "text": text},
        timeout=10,
    )
    resp.raise_for_status()
    body = resp.json()
    if not body.get("ok"):
        raise RuntimeError(f"Slack post to {channel} failed: {body.get('error')}")
