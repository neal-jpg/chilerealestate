from routine.normalize import to_uf, uf_to_usd, normalize_prices

FX = {"uf_clp": 39100.0, "usd_clp": 950.0, "date": "2026-07-02"}


def test_to_uf_handles_each_currency():
    assert to_uf(39100.0, "CLP", FX) == 1.0
    assert to_uf(1.0, "UF", FX) == 1.0
    # 1 USD = 950 CLP = 950/39100 UF
    assert round(to_uf(1.0, "USD", FX), 4) == round(950.0 / 39100.0, 4)


def test_normalize_prices_sets_uf_usd_and_per_m2():
    listing = {"raw_price": 39100.0 * 8900, "currency": "CLP", "m2": 140}
    out = normalize_prices(listing, FX)
    assert out["price_uf"] == 8900
    assert out["price_per_m2_uf"] == round(8900 / 140, 2)
    # usd recomputed from uf, rounded to nearest 1000
    assert out["price_usd"] % 1000 == 0


def test_normalize_prices_handles_missing_m2():
    listing = {"raw_price": 39100.0 * 2400, "currency": "CLP", "m2": None}
    out = normalize_prices(listing, FX)
    assert out["price_uf"] == 2400
    assert out["price_per_m2_uf"] is None
