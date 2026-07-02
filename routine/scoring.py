"""Opportunity scoring: compare each listing's UF/m² to its town+class median.

Medians are segmented by (comuna, class) — never pool houses and land, whose
price/m² live on totally different scales. Region+class is the fallback bucket;
if even that is too thin, the listing is Unrated (we never fake a median).
"""

import statistics

from .config import SAMPLE_GATE, STRONG_RATIO, WATCH_RATIO, PRICE_DROP_TRIGGER


def _active_ppm(listings, key_fn, key):
    return [
        l["price_per_m2_uf"] for l in listings
        if l.get("active", True) and l.get("price_per_m2_uf") is not None and key_fn(l) == key
    ]


def compute_medians(listings):
    """Median UF/m² per (comuna, class) bucket over active, priced listings."""
    buckets = {}
    for l in listings:
        if not l.get("active", True) or l.get("price_per_m2_uf") is None:
            continue
        buckets.setdefault((l["comuna"], l["class"]), []).append(l["price_per_m2_uf"])
    return {k: statistics.median(v) for k, v in buckets.items()}


def _region_medians(listings):
    buckets = {}
    for l in listings:
        if not l.get("active", True) or l.get("price_per_m2_uf") is None:
            continue
        buckets.setdefault((l.get("region"), l["class"]), []).append(l["price_per_m2_uf"])
    return buckets


def _usable(l):
    if l["class"] == "parcela":
        return bool(l.get("water") and l.get("power"))
    return l.get("status") == "Built"


def score_listings(listings):
    """Return listings (copies) with opportunity + opportunity_basis set."""
    comuna_buckets = {}
    for l in listings:
        if l.get("active", True) and l.get("price_per_m2_uf") is not None:
            comuna_buckets.setdefault((l["comuna"], l["class"]), []).append(l["price_per_m2_uf"])
    region_buckets = _region_medians(listings)

    out = []
    for l in listings:
        c = dict(l)
        ppm = c.get("price_per_m2_uf")
        comuna_vals = comuna_buckets.get((c["comuna"], c["class"]), [])
        region_vals = region_buckets.get((c.get("region"), c["class"]), [])

        if ppm is not None and len(comuna_vals) >= SAMPLE_GATE:
            median, basis = statistics.median(comuna_vals), "comuna"
        elif ppm is not None and len(region_vals) >= SAMPLE_GATE:
            median, basis = statistics.median(region_vals), "region"
        else:
            c["opportunity"], c["opportunity_basis"] = "Unrated", "none"
            out.append(c)
            continue

        ratio = ppm / median
        if c.get("price_drop_pct") and c["price_drop_pct"] >= PRICE_DROP_TRIGGER:
            opp = "Strong"
        elif ratio > WATCH_RATIO or not _usable(c):
            opp = "Watch"
        elif ratio <= STRONG_RATIO:
            opp = "Strong"
        else:
            opp = "Fair"
        c["opportunity"], c["opportunity_basis"] = opp, basis
        out.append(c)
    return out
