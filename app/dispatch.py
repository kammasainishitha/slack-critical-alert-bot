import json
import logging
import os
import time

from app.detector import Alert
from app.notifier import alert_on_call

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def run() -> None:
    with open(os.environ["GITHUB_EVENT_PATH"]) as f:
        event = json.load(f)

    payload = event.get("client_payload", {})
    text = payload.get("text", "")
    channel = payload.get("channel", "unknown")
    ts = payload.get("ts") or f"{time.time():.6f}"

    logger.info("Received Slack workflow alert from channel %s: %s", channel, text)

    alert = Alert(
        text=text,
        matched_keyword=payload.get("matched_keyword", "workflow-trigger"),
        ts=ts,
        channel=channel,
    )
    alert_on_call(alert)


if __name__ == "__main__":
    run()
