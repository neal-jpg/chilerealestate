from routine.publish import build_date_from_meta, verify_deploy


def test_build_date_from_meta_parses_or_none():
    assert build_date_from_meta('{"build_date": "2026-07-02"}') == "2026-07-02"
    assert build_date_from_meta("not json") is None
    assert build_date_from_meta('{"other": 1}') is None


def test_verify_deploy_succeeds_after_one_retrigger():
    calls = {"check": 0, "retrigger": 0}
    def check():
        calls["check"] += 1
        return "2026-07-02" if calls["check"] >= 2 else "old"   # stale first, then fresh
    def retrigger():
        calls["retrigger"] += 1
    ok = verify_deploy("2026-07-02", check, retrigger, attempts=3, wait_fn=lambda: None)
    assert ok is True
    assert calls["retrigger"] == 1


def test_verify_deploy_gives_up_after_attempts():
    ok = verify_deploy("target", lambda: "stale", lambda: None, attempts=2, wait_fn=lambda: None)
    assert ok is False
