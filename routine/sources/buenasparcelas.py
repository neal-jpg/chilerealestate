"""Scrape BuenasParcelas.cl — a Wix site whose listing data lives in an embedded
`wix-warmup-data` JSON collection (LoteosParcelaciones, all parcelas).

Pure parsers here; the warmup extraction, record mapping, and network fetch are
in the second half (Task 4). Field formats captured from the live site."""

import re

_FEATURE_FIELDS = ("agua", "luz", "crditoDirecto", "hipotecario")


def wix_image_url(uri):
    """wix:image://v1/<mediaId>/... -> static.wixstatic.com hotlink, or ''."""
    m = re.match(r"wix:image://v1/([^/]+)/", uri or "")
    return f"https://static.wixstatic.com/media/{m.group(1)}" if m else ""


def parse_price_clp(s):
    """'$18.000.000' -> 18000000 (int CLP)."""
    digits = re.sub(r"[^0-9]", "", s or "")
    return int(digits) if digits else None


def parse_area_m2(s):
    """'✓ 5.000 m²' -> 5000, or None when no m² number is present."""
    if not s:
        return None
    m = re.search(r"([0-9][0-9.]*)\s*m", s)
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
    return "Built" if "Terminado" in (ventatipo or "") else "Project"
