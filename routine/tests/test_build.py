from routine.build import build

FX = {"uf_clp": 39100.0, "usd_clp": 950.0, "date": "2026-07-02"}


def _raw(url, comuna, klass, uf, source="BuenasParcelas", m2=100, **kw):
    d = {
        "url": url, "title": f"L {url}", "source": source, "region": "X",
        "comuna": comuna, "class": klass, "type": "House" if klass == "turnkey" else "Parcela",
        "status": "Built", "raw_price": uf * FX["uf_clp"], "currency": "CLP",
        "m2": m2, "water": True, "power": True, "access": None, "image_url": "",
    }
    d.update(kw)
    return d


def test_build_produces_contract_shaped_listings():
    raw = [_raw("a", "Pucón", "turnkey", 8900, m2=140)]
    result = build(raw, existing_listings=[], existing_snapshots={}, fx=FX,
                   run_date="2026-07-01")
    l = result["listings"][0]
    for field in ("id", "price_uf", "price_usd", "price_per_m2_uf", "yield_band",
                  "opportunity", "opportunity_basis", "price_drop_pct",
                  "first_seen", "last_seen", "active"):
        assert field in l
    assert l["id"] == "a"
    assert l["price_uf"] == 8900
    assert l["yield_band"] == "~4–8% gross · seasonal"  # Pucón turnkey


def test_build_meta_flags_thin_regions_and_lists_regions():
    raw = [_raw("a", "Pucón", "turnkey", 8900)]  # region X has 1 active -> thin
    result = build(raw, [], {}, FX, run_date="2026-07-01")
    assert result["meta"]["build_date"] == "2026-07-01"
    assert [r["code"] for r in result["meta"]["regions"]] == ["IX", "XIV", "X"]
    assert "X" in result["meta"]["thin_coverage"]


def test_build_fx_passthrough():
    result = build([], [], {}, FX, run_date="2026-07-01")
    assert result["fx"] == FX


from routine.build import collect_raw


def test_collect_raw_merges_scraper_and_alert_sources():
    bp = [{"url": "bp1", "source": "BuenasParcelas"}]
    al = [{"url": "al1", "source": "Yapo"}]
    combined = collect_raw(bp_listings=bp, alert_listings=al)
    urls = {r["url"] for r in combined}
    assert urls == {"bp1", "al1"}


def test_collect_raw_dedups_by_url_preferring_alert():
    # if both sources somehow emit the same url, keep one (alert wins — richer)
    bp = [{"url": "dup", "source": "BuenasParcelas"}]
    al = [{"url": "dup", "source": "Yapo"}]
    combined = collect_raw(bp_listings=bp, alert_listings=al)
    assert len(combined) == 1
    assert combined[0]["source"] == "Yapo"
