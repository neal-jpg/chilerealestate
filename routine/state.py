"""Small persisted state for the routine (currently just the alert watermark)."""

import json
import os

DEFAULT = {"alert_watermark": ""}


def load_state(path):
    if not os.path.exists(path):
        return dict(DEFAULT)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    merged = dict(DEFAULT)
    merged.update(data)
    return merged


def save_state(path, state):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
