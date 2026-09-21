import json
from pathlib import Path
from typing import Optional

STATE_PATH = Path(__file__).resolve().parent.parent / "state" / "state.json"
_MAX_PROCESSED_PER_CHANNEL = 500


def _load() -> dict:
    if not STATE_PATH.exists():
        return {"last_ts": {}, "processed": {}}
    with open(STATE_PATH) as f:
        return json.load(f)


def _save(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2, sort_keys=True)


def get_last_ts(channel: str) -> Optional[str]:
    return _load()["last_ts"].get(channel)


def set_last_ts(channel: str, ts: str) -> None:
    state = _load()
    state["last_ts"][channel] = ts
    _save(state)


def already_processed(channel: str, ts: str) -> bool:
    return ts in _load()["processed"].get(channel, [])


def mark_processed(channel: str, ts: str) -> None:
    state = _load()
    processed = state["processed"].setdefault(channel, [])
    if ts not in processed:
        processed.append(ts)
    state["processed"][channel] = processed[-_MAX_PROCESSED_PER_CHANNEL:]
    _save(state)


def log_call(channel: str, ts: str, name: str, phone: str, call_sid: Optional[str], status: str) -> None:
    state = _load()
    calls = state.setdefault("calls", [])
    calls.append(
        {
            "channel": channel,
            "ts": ts,
            "name": name,
            "phone": phone,
            "call_sid": call_sid,
            "status": status,
        }
    )
    state["calls"] = calls[-200:]
    _save(state)
