from routine.publish import build_date_from_meta, verify_deploy


def test_build_date_from_meta_parses_or_none():
    assert build_date_from_meta('{"build_date": "2026-07-02"}') == "2026-07-02"
    assert build_date_from_meta("not json") is None
    assert build_date_from_meta('{"other": 1}') is None


def test_verify_deploy_succeeds_while_polling_without_retrigger():
    calls = {"check": 0, "retrigger": 0}
    def check():
        calls["check"] += 1
        return "d" if calls["check"] >= 3 else "stale"   # deploy lands on the 3rd poll
    def retrigger():
        calls["retrigger"] += 1
    ok = verify_deploy("d", check, retrigger, attempts=2, polls=5, poll_seconds=0, sleep_fn=lambda s: None)
    assert ok is True
    assert calls["retrigger"] == 0   # landed during polling -> no spurious retrigger


def test_verify_deploy_retriggers_only_when_deploy_never_lands():
    calls = {"check": 0, "retrigger": 0}
    def check():
        calls["check"] += 1
        return "d" if calls["check"] > 5 else "stale"   # stale for all 5 polls of attempt 1
    def retrigger():
        calls["retrigger"] += 1
    ok = verify_deploy("d", check, retrigger, attempts=2, polls=5, poll_seconds=0, sleep_fn=lambda s: None)
    assert ok is True
    assert calls["retrigger"] == 1   # retriggered once after attempt 1 failed to land


def test_verify_deploy_gives_up_after_attempts():
    ok = verify_deploy("target", lambda: "stale", lambda: None,
                       attempts=2, polls=2, poll_seconds=0, sleep_fn=lambda s: None)
    assert ok is False
