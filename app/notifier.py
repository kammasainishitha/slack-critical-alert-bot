import logging
import time
from xml.sax.saxutils import escape

from twilio.rest import Client

from app.config import (
    CALL_STAGGER_SECONDS,
    ON_CALL,
    TWILIO_ACCOUNT_SID,
    TWILIO_AUTH_TOKEN,
    TWILIO_FROM_NUMBER,
)
from app.detector import Alert
from app.state import log_call

logger = logging.getLogger(__name__)

_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def _recipients_for(alert: Alert):
    text_lower = alert.text.lower()
    for entry in ON_CALL:
        match_keywords = entry.get("match_keywords")
        if match_keywords and not any(kw.lower() in text_lower for kw in match_keywords):
            continue
        yield entry


def _build_twiml(alert: Alert) -> str:
    message = (
        f"Alert. An urgent ticket was just created in Slack. "
        f"Message text: {alert.text}. Please check Slack immediately."
    )
    return f'<Response><Say voice="alice" loop="2">{escape(message)}</Say></Response>'


def alert_on_call(alert: Alert) -> None:
    recipients = list(_recipients_for(alert))
    if not recipients:
        logger.warning("No on-call recipients matched alert: %s", alert)
        return

    twiml = _build_twiml(alert)

    for i, recipient in enumerate(recipients):
        if i > 0:
            time.sleep(CALL_STAGGER_SECONDS)
        try:
            call = _client.calls.create(
                twiml=twiml,
                to=recipient["phone"],
                from_=TWILIO_FROM_NUMBER,
            )
            logger.info("Called %s (%s): sid=%s", recipient["name"], recipient["phone"], call.sid)
            log_call(alert.channel, alert.ts, recipient["name"], recipient["phone"], call.sid, call.status)
        except Exception:
            logger.exception("Failed to call %s (%s)", recipient["name"], recipient["phone"])
            log_call(alert.channel, alert.ts, recipient["name"], recipient["phone"], None, "failed")
