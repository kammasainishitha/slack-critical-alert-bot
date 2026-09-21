import requests

from app.config import SLACK_BOT_TOKEN

_API_URL = "https://slack.com/api/conversations.history"


def fetch_new_messages(channel: str, oldest: str) -> list[dict]:
    """Messages posted strictly after `oldest`, ascending by ts."""
    resp = requests.get(
        _API_URL,
        headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
        params={"channel": channel, "oldest": oldest, "limit": 200},
        timeout=15,
    )
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Slack API error for channel {channel}: {data.get('error')}")

    messages = [
        m for m in data.get("messages", [])
        if m.get("type") == "message" and not m.get("subtype")
    ]
    messages.sort(key=lambda m: float(m["ts"]))
    return messages
