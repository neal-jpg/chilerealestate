from routine.resilience import resolve_fx, safe_collect, should_write


def test_resolve_fx_returns_live_when_available():
    assert resolve_fx(lambda: {"uf_clp": 1}, None) == {"uf_clp": 1}


def test_resolve_fx_falls_back_to_cache_on_failure():
    def boom():
        raise RuntimeError("mindicador down")
    assert resolve_fx(boom, {"uf_clp": 999}) == {"uf_clp": 999}


def test_resolve_fx_raises_when_no_cache():
    def boom():
        raise RuntimeError("down")
    try:
        resolve_fx(boom, None)
        assert False, "expected raise"
    except RuntimeError:
        pass


def test_safe_collect_swallows_failure():
    assert safe_collect(lambda: [1, 2]) == [1, 2]
    assert safe_collect(lambda: (_ for _ in ()).throw(RuntimeError("x"))) == []


def test_should_write_blocks_blanking_the_site():
    prev = [{"active": True}, {"active": True}]
    assert should_write([{"active": True}], prev) is True     # still has listings -> write
    assert should_write([{"active": False}], prev) is False   # would go to 0 active -> skip
    assert should_write([], prev) is False                    # empty -> skip
    assert should_write([], []) is True                       # nothing before -> fine to write (first run)
