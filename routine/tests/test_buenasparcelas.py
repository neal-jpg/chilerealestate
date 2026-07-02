from routine.sources.buenasparcelas import (
    wix_image_url, parse_price_clp, parse_area_m2, feature_flags, parse_status,
)


def test_wix_image_url_converts_uri():
    uri = "wix:image://v1/cdc54a_abc~mv2.jpg/name.jpg#originWidth=10"
    assert wix_image_url(uri) == "https://static.wixstatic.com/media/cdc54a_abc~mv2.jpg"
    assert wix_image_url("") == ""
    assert wix_image_url(None) == ""


def test_parse_price_clp_strips_symbols():
    assert parse_price_clp("$18.000.000") == 18000000
    assert parse_price_clp("$20.900.000") == 20900000


def test_parse_area_m2_extracts_number_with_dot_thousands():
    assert parse_area_m2("✓ 5.000 m²") == 5000
    assert parse_area_m2(None) is None
    assert parse_area_m2("consultar") is None


def test_feature_flags_scan_all_fields_not_names():
    # jumbled: agua field holds "Luz", hipotecario holds "Agua"
    rec = {"agua": "✓ Luz", "crditoDirecto": "✓ Hipotecario", "hipotecario": "✓ Agua"}
    water, power = feature_flags(rec)
    assert water is True   # "Agua" appears somewhere
    assert power is True   # "Luz" appears somewhere
    rec2 = {"agua": "✓ Agua"}
    assert feature_flags(rec2) == (True, False)


def test_parse_status_maps_ventatipo():
    assert parse_status("☺Terminado") == "Built"
    assert parse_status("►En Proceso") == "Project"
    assert parse_status("anything else") == "Project"  # default to Project
