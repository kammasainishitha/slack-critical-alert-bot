import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent

with open(ROOT / "config.yaml") as f:
    CONFIG = yaml.safe_load(f)

# Only required by the Slack-API polling path (app/poll.py). The
# Workflow-Builder dispatch path (app/dispatch.py) doesn't need it.
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")

TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_FROM_NUMBER = os.environ["TWILIO_FROM_NUMBER"]

WATCHED_CHANNELS = list(CONFIG["watched_channels"])
KEYWORDS = [k.lower() for k in CONFIG["keywords"]]
PRIORITY_FIELD_VALUES = [v.lower() for v in CONFIG["priority_field_values"]]
ON_CALL = CONFIG["on_call"]
CALL_STAGGER_SECONDS = CONFIG.get("call_stagger_seconds", 5)
