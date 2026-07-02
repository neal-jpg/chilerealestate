"""Scrape BuenasParcelas.cl — a Wix site whose listing data lives in an embedded
`wix-warmup-data` JSON collection (LoteosParcelaciones, all parcelas).

Pure parsers here; the warmup extraction, record mapping, and network fetch are
in the second half (Task 4). Field formats captured from the live site."""

import json
import re
import urllib.request

from ..config import BUENASPARCELAS_URL

_FEATURE_FIELDS = ("agua", "luz", "crditoDirecto", "hipotecario")


def wix_image_url(uri):
    """wix:image://v1/<mediaId>/... -> static.wixstatic.com hotlink, or ''."""
    m = re.match(r"wix:image://v1/([^/]+)/", "" if uri is None else str(uri))
    return f"https://static.wixstatic.com/media/{m.group(1)}" if m else ""


def parse_price_clp(s):
    """'$18.000.000' -> 18000000 (int CLP). Coerces non-str input, never crashes."""
    digits = re.sub(r"[^0-9]", "", "" if s is None else str(s))
    return int(digits) if digits else None


def parse_area_m2(s):
    """'✓ 5.000 m²' -> 5000, or None when no m² number is present."""
    if s is None:
        return None
    m = re.search(r"([0-9][0-9.]*)\s*m", str(s))
    if not m:
        return None
    return int(m.group(1).replace(".", ""))


def feature_flags(record):
    """(water, power) by scanning ALL feature-field VALUES for Agua/Luz —
    the site mislabels these fields, so field names are not trustworthy."""
    blob = " ".join(str(record.get(f) or "") for f in _FEATURE_FIELDS)
    return ("Agua" in blob, "Luz" in blob)


def parse_status(ventatipo):
    """'☺Terminado' -> 'Built'; '►En Proceso' (or anything else) -> 'Project'."""
    return "Built" if "Terminado" in str(ventatipo or "") else "Project"


_WARMUP_RE = re.compile(
    r'<script[^>]*id="wix-warmup-data"[^>]*>(.*?)</script>', re.S)
_COLLECTION = "LoteosParcelaciones"
_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36")


def extract_warmup(html):
    """Pull the wix-warmup-data JSON object out of the page HTML, or None."""
    m = _WARMUP_RE.search(html or "")
    if not m:
        return None
    try:
        return json.loads(m.group(1).strip())
    except ValueError:
        return None


def record_to_raw(record, town_region):
    """Map one LoteosParcelaciones record to a raw-listing dict, or None if the
    town is outside the active regions (or the record lacks a url/price)."""
    ciudad = (record.get("ciudad") or "").strip()
    mapped = town_region.get(ciudad)
    url = record.get("url")
    price = parse_price_clp(record.get("valor"))
    if not mapped or not url or price is None:
        return None
    region, comuna = mapped
    water, power = feature_flags(record)
    return {
        "url": url,
        "title": (record.get("title") or "").strip(),
        "source": "BuenasParcelas",
        "region": region,
        "comuna": comuna,
        "class": "parcela",
        "type": "Parcela",
        "status": parse_status(record.get("VentaTipo")),
        "raw_price": price,
        "currency": "CLP",
        "m2": parse_area_m2(record.get("area")),
        "water": water,
        "power": power,
        "access": None,
        "image_url": wix_image_url(record.get("imagen")),
    }


def listings_from_warmup(warmup, town_region):
    """All in-region parcela raw-listings from a parsed warmup payload."""
    try:
        records = warmup["appsWarmupData"]["dataBinding"]["dataStore"][
            "recordsByCollectionId"][_COLLECTION]
    except (KeyError, TypeError):
        return []
    out = []
    for rec in records.values():
        try:
            raw = record_to_raw(rec, town_region)
        except Exception:
            continue  # one malformed record must never take down the whole batch
        if raw is not None:
            out.append(raw)
    return out


def fetch_html(url=BUENASPARCELAS_URL):
    """Network shell — fetch the page HTML. Not unit-tested."""
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=40) as resp:
        return resp.read().decode("utf-8", errors="replace")


def collect(town_region, url=BUENASPARCELAS_URL):
    """Fetch + parse -> raw-listings. Network shell (calls fetch_html)."""
    html = fetch_html(url)
    warmup = extract_warmup(html)
    return listings_from_warmup(warmup, town_region) if warmup else []
