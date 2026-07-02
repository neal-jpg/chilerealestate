"""Turn forwarded Yapo/Portal alert emails into raw-listing dicts.

Make.com drops each alert email as a row into a Google Sheet published as CSV
(columns: received_at, sender, subject, body). This module reads that CSV, and
for each new row asks Claude to extract the listings. The model call itself is
injected (`model_call`) so the pure parts — CSV reading, prompt building,
response parsing — are fully testable without the network."""

import csv
import io
import json
import re

RAW_FIELDS = ("url", "title", "source", "region", "comuna", "class", "type",
              "status", "raw_price", "currency", "m2", "water", "power",
              "access", "image_url")

_PROMPT = """You are extracting real-estate listings from a {sender} alert email.

Return ONLY a JSON array (no prose). One object per property in the email, each with:
- url (the listing link), title, source ("Yapo" or "Portal")
- region ("IX" Araucanía, "XIV" Los Ríos, "X" Los Lagos), comuna (town, accented)
- class ("turnkey" for houses/apartments/cabins, "parcela" for land)
- type (House/Apartment/Cabin/Parcela/Land), status ("Built" or "Project")
- raw_price (number only), currency ("UF", "CLP", or "USD")
- m2 (number or null), water (bool), power (bool), access (bool or null)
- image_url (string or "")

If a field is unknown use null (or "" for image_url, false for water/power).
Skip anything not in regions IX/XIV/X. Email body:

{body}
"""


def read_alert_csv(csv_text):
    """Parse the published-CSV alert inbox into a list of row dicts."""
    return list(csv.DictReader(io.StringIO(csv_text)))


def new_rows(rows, watermark):
    """Rows whose received_at is strictly greater than the watermark string."""
    return [r for r in rows if (r.get("received_at") or "") > (watermark or "")]


def build_extraction_prompt(email_body, sender):
    src = "Yapo" if "yapo" in (sender or "").lower() else "Portal"
    return _PROMPT.format(sender=src, body=email_body)


def parse_extraction_response(text):
    """Parse the model's reply into a list of dicts. Tolerates code fences and
    surrounding prose by extracting the first top-level [...] array. Returns []
    on anything that isn't a JSON array of objects."""
    if not text:
        return []
    fenced = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.S)
    candidate = fenced.group(1) if fenced else None
    if candidate is None:
        m = re.search(r"\[.*\]", text, re.S)
        candidate = m.group(0) if m else None
    if candidate is None:
        return []
    try:
        data = json.loads(candidate)
    except ValueError:
        return []
    return data if isinstance(data, list) else []
