from routine.fx import parse_mindicador


def test_parse_mindicador_extracts_uf_usd_and_date():
    payload = {
        "uf": {"codigo": "uf", "fecha": "2026-07-02T00:00:00.000", "valor": 39100.5},
        "dolar": {"codigo": "dolar", "fecha": "2026-07-02T00:00:00.000", "valor": 950.3},
    }
    fx = parse_mindicador(payload)
    assert fx["uf_clp"] == 39100.5
    assert fx["usd_clp"] == 950.3
    assert fx["date"] == "2026-07-02"
