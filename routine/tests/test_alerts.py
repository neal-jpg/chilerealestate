import os
from routine.sources.alerts import (
    read_alert_csv, new_rows, build_extraction_prompt, parse_extraction_response,
)

FIX = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures", "alert_sample.txt")


def test_read_alert_csv_parses_rows():
    csv_text = (
        "received_at,sender,subject,body\r\n"
        "2026-07-01T09:00:00,alertas@yapo.cl,Nuevas,Casa en Pucón UF 8900\r\n"
        "2026-07-02T09:00:00,alertas@portalinmobiliario.cl,Match,Depto en Valdivia\r\n"
    )
    rows = read_alert_csv(csv_text)
    assert len(rows) == 2
    assert rows[0]["sender"] == "alertas@yapo.cl"
    assert rows[1]["body"] == "Depto en Valdivia"


def test_new_rows_filters_by_watermark():
    rows = [
        {"received_at": "2026-07-01T09:00:00", "body": "a"},
        {"received_at": "2026-07-02T09:00:00", "body": "b"},
    ]
    assert [r["body"] for r in new_rows(rows, "2026-07-01T09:00:00")] == ["b"]
    assert len(new_rows(rows, "")) == 2  # empty watermark -> all rows new


def test_build_extraction_prompt_includes_body_and_shape():
    body = open(FIX, encoding="utf-8").read()
    prompt = build_extraction_prompt(body, "alertas@yapo.cl")
    assert "Yapo" in prompt or "yapo" in prompt
    assert "JSON" in prompt
    assert "raw_price" in prompt and "currency" in prompt  # asks for the contract
    assert "Pucón" in prompt  # the email body is embedded


def test_parse_extraction_response_reads_json_array():
    text = '[{"url":"u1","raw_price":8900,"currency":"UF","comuna":"Pucón"}]'
    out = parse_extraction_response(text)
    assert out == [{"url": "u1", "raw_price": 8900, "currency": "UF", "comuna": "Pucón"}]


def test_parse_extraction_response_tolerates_code_fences_and_prose():
    text = 'Here you go:\n```json\n[{"url":"u1"}]\n```\nDone.'
    assert parse_extraction_response(text) == [{"url": "u1"}]


def test_parse_extraction_response_bad_input_returns_empty():
    assert parse_extraction_response("no json here") == []
    assert parse_extraction_response('{"not":"an array"}') == []


from routine.sources.alerts import extract_from_email, collect_alerts


def _fake_model(prompt):
    # ignores the prompt; returns a fixed listing so we test composition, not the model
    return '[{"url":"https://yapo.cl/x1","raw_price":8900,"currency":"UF","comuna":"Pucón","class":"turnkey","source":"Yapo"}]'


def test_extract_from_email_uses_model_call():
    out = extract_from_email("body text", "alertas@yapo.cl", _fake_model)
    assert out[0]["url"] == "https://yapo.cl/x1"


def test_collect_alerts_processes_new_rows_and_advances_watermark():
    csv_text = (
        "received_at,sender,subject,body\r\n"
        "2026-07-01T09:00:00,alertas@yapo.cl,S,old email\r\n"
        "2026-07-02T09:00:00,alertas@yapo.cl,S,new email\r\n"
    )
    listings, new_wm = collect_alerts(csv_text, "2026-07-01T09:00:00", _fake_model)
    assert len(listings) == 1                       # only the 2026-07-02 row is new
    assert new_wm == "2026-07-02T09:00:00"          # watermark advanced to newest processed
    # nothing new -> no listings, watermark unchanged
    listings2, wm2 = collect_alerts(csv_text, new_wm, _fake_model)
    assert listings2 == [] and wm2 == new_wm


def test_extract_from_email_drops_malformed_and_stamps_source():
    def bad_model(prompt):
        # one good, one missing url, one bad currency, one string price (coerced)
        return ('[{"url":"u1","raw_price":8900,"currency":"UF","source":"WRONG"},'
                '{"raw_price":5000,"currency":"UF"},'                       # no url -> drop
                '{"url":"u3","raw_price":100,"currency":"BTC"},'            # bad currency -> drop
                '{"url":"u4","raw_price":"185.000.000","currency":"CLP"}]')  # string price -> coerced
    out = extract_from_email("body", "alertas@yapo.cl", bad_model)
    assert len(out) == 2
    assert {r["url"] for r in out} == {"u1", "u4"}
    # source stamped from the sender (Yapo), NOT the model's "WRONG"
    assert all(r["source"] == "Yapo" for r in out)
    # string price coerced to int
    u4 = next(r for r in out if r["url"] == "u4")
    assert u4["raw_price"] == 185000000


def test_extract_from_email_returns_full_contract_keys():
    def model(prompt):
        return '[{"url":"u1","raw_price":8900,"currency":"UF"}]'
    out = extract_from_email("body", "alertas@portalinmobiliario.cl", model)
    for k in ("url", "title", "source", "region", "comuna", "class", "type",
              "status", "raw_price", "currency", "m2", "water", "power",
              "access", "image_url"):
        assert k in out[0]
    assert out[0]["source"] == "Portal"  # sender is portal
