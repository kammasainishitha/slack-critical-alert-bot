import re
from dataclasses import dataclass
from typing import Optional

from app.config import KEYWORDS, PRIORITY_FIELD_VALUES

_WORD_RE_CACHE = {kw: re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE) for kw in KEYWORDS}


@dataclass
class Alert:
    text: str
    matched_keyword: str
    ts: str
    channel: str
    permalink: Optional[str] = None


def _text_matches_keyword(text: str) -> Optional[str]:
    for kw, pattern in _WORD_RE_CACHE.items():
        if pattern.search(text):
            return kw
    return None


def _priority_field_matches(event: dict) -> Optional[str]:
    for block in event.get("blocks") or []:
        for field in block.get("fields") or []:
            field_text = (field.get("text") or "").lower()
            for value in PRIORITY_FIELD_VALUES:
                if f"priority" in field_text and value in field_text:
                    return value
    for attachment in event.get("attachments") or []:
        for field in attachment.get("fields") or []:
            field_title = (field.get("title") or "").lower()
            field_value = (field.get("value") or "").lower()
            if "priority" in field_title:
                for value in PRIORITY_FIELD_VALUES:
                    if value in field_value:
                        return value
    return None


def detect(event: dict) -> Optional[Alert]:
    text = event.get("text", "")

    matched = _text_matches_keyword(text) or _priority_field_matches(event)
    if not matched:
        return None

    return Alert(
        text=text,
        matched_keyword=matched,
        ts=event["ts"],
        channel=event["channel"],
    )
