"""Opportunity scoring: compare each listing's UF/m² to its town+class median.

Medians are segmented by (comuna, class) — never pool houses and land, whose
price/m² live on totally different scales. Region+class is the fallback bucket;
if even that is too thin, the listing is Unrated (we never fake a median).
"""

import statistics

from .config import SAMPLE_GATE, STRONG_RATIO, WATCH_RATIO, PRICE_DROP_TRIGGER


def _bucket(listings, key_fn):
    """Group active, priced listings' UF/m² values by key_fn(listing)."""
    buckets = {}
    for l in listings:
        if not l.get("active", True) or l.get("price_per_m2_uf") is None:
            continue
        buckets.setdefault(key_fn(l), []).append(l["price_per_m2_uf"])
    return buckets


def compute_medians(listings):
    """Median UF/m² per (comuna, class) bucket over active, priced listings."""
    buckets = _bucket(listings, lambda l: (l["comuna"], l["class"]))
    return {k: statistics.median(v) for k, v in buckets.items()}


def _usable(l):
    if l["class"] == "parcela":
        return bool(l.get("water") and l.get("power"))
    return l.get("status") == "Built"


def score_listings(listings):
    """Return listings (copies) with opportunity + opportunity_basis set."""
    comuna_buckets = _bucket(listings, lambda l: (l["comuna"], l["class"]))
    region_buckets = _bucket(listings, lambda l: (l.get("region"), l["class"]))
    comuna_medians = {k: statistics.median(v) for k, v in comuna_buckets.items()}
    region_medians = {k: statistics.median(v) for k, v in region_buckets.items()}

    out = []
    for l in listings:
        c = dict(l)
        ppm = c.get("price_per_m2_uf")
        ck = (c["comuna"], c["class"])
        rk = (c.get("region"), c["class"])

        if ppm is not None and len(comuna_buckets.get(ck, [])) >= SAMPLE_GATE:
            median, basis = comuna_medians[ck], "comuna"
        elif ppm is not None and len(region_buckets.get(rk, [])) >= SAMPLE_GATE:
            median, basis = region_medians[rk], "region"
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
