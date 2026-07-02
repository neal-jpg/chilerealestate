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


import json
import os
from routine.sources.buenasparcelas import (
    extract_warmup, listings_from_warmup, record_to_raw,
)
from routine import config

FIX = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures", "bp_warmup_sample.json")


def test_record_to_raw_maps_all_fields():
    rec = {
        "title": "Robles", "url": "https://www.buenasparcelas.cl/robles",
        "valor": "$20.900.000", "ciudad": "Pucon", "area": "✓ 5.000 m²",
        "VentaTipo": "►En Proceso", "agua": "✓ Agua", "luz": "✓ Luz",
        "imagen": "wix:image://v1/abc~mv2.jpg/n.jpg#x=1",
    }
    raw = record_to_raw(rec, config.TOWN_REGION)
    assert raw["source"] == "BuenasParcelas"
    assert raw["url"] == "https://www.buenasparcelas.cl/robles"
    assert raw["region"] == "IX" and raw["comuna"] == "Pucón"  # canonical accent
    assert raw["class"] == "parcela" and raw["type"] == "Parcela"
    assert raw["raw_price"] == 20900000 and raw["currency"] == "CLP"
    assert raw["m2"] == 5000 and raw["status"] == "Project"
    assert raw["water"] is True and raw["power"] is True and raw["access"] is None
    assert raw["image_url"] == "https://static.wixstatic.com/media/abc~mv2.jpg"


def test_record_to_raw_drops_out_of_region_town():
    rec = {"url": "u", "ciudad": "Talca", "valor": "$1.000.000"}
    assert record_to_raw(rec, config.TOWN_REGION) is None


def test_extract_warmup_and_listings_from_fixture():
    payload = json.load(open(FIX, encoding="utf-8"))
    listings = listings_from_warmup(payload, config.TOWN_REGION)
    # 3 records in fixture, 1 is Talca (out of region) -> 2 kept
    assert len(listings) == 2
    urls = {l["url"] for l in listings}
    assert "https://www.buenasparcelas.cl/talca-parcela" not in urls
    # Tegualda record's jumbled utility fields still resolve to water+power
    teg = next(l for l in listings if "rioexpedicion" in l["url"])
    assert teg["water"] is True and teg["power"] is True
    assert teg["comuna"] == "Tegualda" and teg["region"] == "X"


def test_extract_warmup_from_html_script_tag():
    html = '<html><body><script id="wix-warmup-data" type="application/json">{"a":1}</script></body></html>'
    assert extract_warmup(html) == {"a": 1}
    assert extract_warmup("<html>no warmup</html>") is None
