import logging
import time

from app.config import WATCHED_CHANNELS
from app.detector import detect
from app.notifier import alert_on_call
from app.slack_client import fetch_new_messages
from app.state import already_processed, get_last_ts, mark_processed, set_last_ts

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def run() -> None:
    for channel in WATCHED_CHANNELS:
        last_ts = get_last_ts(channel)

        if last_ts is None:
            # First run for this channel: don't alert on history, just set
            # the watermark so future runs only see new messages.
            logger.info("Bootstrapping watermark for channel %s", channel)
            set_last_ts(channel, f"{time.time():.6f}")
            continue

        try:
            messages = fetch_new_messages(channel, oldest=last_ts)
        except Exception:
            logger.exception("Failed to fetch messages for channel %s", channel)
            continue

        if not messages:
            continue

        newest_ts = last_ts
        for message in messages:
            ts = message["ts"]
            if already_processed(channel, ts):
                continue
            mark_processed(channel, ts)

            message["channel"] = channel
            alert = detect(message)
            if alert:
                logger.info("Detected urgent/critical message in %s: %s", channel, alert.text)
                alert_on_call(alert)

            if float(ts) > float(newest_ts):
                newest_ts = ts

        set_last_ts(channel, newest_ts)


if __name__ == "__main__":
    run()
