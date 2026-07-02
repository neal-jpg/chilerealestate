from routine.yield_bands import apply_yield_bands


def test_turnkey_gets_town_band_parcela_gets_none():
    listings = [
        {"comuna": "Pucón", "class": "turnkey"},
        {"comuna": "Pucón", "class": "parcela"},
        {"comuna": "Nowhere", "class": "turnkey"},
    ]
    out = apply_yield_bands(listings, {"Pucón": "~4–8% gross · seasonal"})
    assert out[0]["yield_band"] == "~4–8% gross · seasonal"
    assert out[1]["yield_band"] is None
    assert out[2]["yield_band"] is None  # turnkey but no band configured
