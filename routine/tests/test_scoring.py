from routine.scoring import compute_medians, score_listings


def _mk(id, comuna, klass, ppm, active=True, status="Built", water=True, power=True, drop=None):
    return {
        "id": id, "comuna": comuna, "class": klass, "price_per_m2_uf": ppm,
        "active": active, "status": status, "water": water, "power": power,
        "price_drop_pct": drop,
    }


def test_compute_medians_buckets_by_comuna_and_class():
    listings = [
        _mk("a", "Pucón", "turnkey", 60),
        _mk("b", "Pucón", "turnkey", 70),
        _mk("c", "Pucón", "parcela", 0.5),
    ]
    medians = compute_medians(listings)
    assert medians[("Pucón", "turnkey")] == 65
    assert medians[("Pucón", "parcela")] == 0.5


def test_unrated_when_too_few_comps():
    # 1 comp, below SAMPLE_GATE and no region fallback bucket size either
    listings = [_mk("a", "Pucón", "turnkey", 60)]
    scored = score_listings(listings)
    assert scored[0]["opportunity"] == "Unrated"
    assert scored[0]["opportunity_basis"] == "none"


def test_strong_fair_watch_by_ratio():
    # 5 turnkey comps in Pucón so the gate passes; median is 100
    comps = [_mk(f"c{i}", "Pucón", "turnkey", 100) for i in range(5)]
    cheap = _mk("cheap", "Pucón", "turnkey", 80)      # 0.8x -> Strong (usable)
    mid = _mk("mid", "Pucón", "turnkey", 100)          # 1.0x -> Fair
    dear = _mk("dear", "Pucón", "turnkey", 130)        # 1.3x -> Watch
    scored = {l["id"]: l for l in score_listings(comps + [cheap, mid, dear])}
    assert scored["cheap"]["opportunity"] == "Strong"
    assert scored["mid"]["opportunity"] == "Fair"
    assert scored["dear"]["opportunity"] == "Watch"


def test_price_drop_forces_strong():
    comps = [_mk(f"c{i}", "Pucón", "turnkey", 100) for i in range(5)]
    dropped = _mk("d", "Pucón", "turnkey", 130, drop=6)  # dear but dropped -> Strong
    scored = {l["id"]: l for l in score_listings(comps + [dropped])}
    assert scored["d"]["opportunity"] == "Strong"


def test_parcela_missing_utilities_is_watch():
    comps = [_mk(f"c{i}", "Frutillar", "parcela", 1.0, status="Project") for i in range(5)]
    bad = _mk("b", "Frutillar", "parcela", 0.7, status="Project", water=False, power=False)
    scored = {l["id"]: l for l in score_listings(comps + [bad])}
    assert scored["b"]["opportunity"] == "Watch"


def test_region_fallback_when_comuna_thin_but_region_has_comps():
    # 5 turnkey comps across 5 distinct comunas: no single comuna bucket hits
    # the gate, but the (region, class) bucket does, so scoring falls back to
    # the region median and stamps basis="region".
    comps = [_mk(f"c{i}", f"Town{i}", "turnkey", 100) for i in range(5)]
    target = _mk("t", "Town0", "turnkey", 80)  # Town0 comuna bucket = 2 (<5)
    scored = {l["id"]: l for l in score_listings(comps + [target])}
    assert scored["t"]["opportunity_basis"] == "region"
    assert scored["t"]["opportunity"] == "Strong"  # 0.8x of median, usable
