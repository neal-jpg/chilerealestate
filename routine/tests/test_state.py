import json
import os
from routine.state import load_state, save_state


def test_load_state_defaults_when_absent(tmp_path):
    st = load_state(str(tmp_path / "nope.json"))
    assert st == {"alert_watermark": ""}


def test_save_then_load_roundtrips(tmp_path):
    p = str(tmp_path / "state.json")
    save_state(p, {"alert_watermark": "2026-07-02T09:00:00"})
    assert load_state(p)["alert_watermark"] == "2026-07-02T09:00:00"
