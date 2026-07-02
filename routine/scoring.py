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
    """Return listings (copies) with opportunity, opportunity_basis, and a
    one-sentence opportunity_reason set (the reason is derived from the same
    ratio/median facts, so it always matches the tag)."""
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
        noun = "parcela" if c["class"] == "parcela" else "home"

        if ppm is not None and len(comuna_buckets.get(ck, [])) >= SAMPLE_GATE:
            median, basis = comuna_medians[ck], "comuna"
        elif ppm is not None and len(region_buckets.get(rk, [])) >= SAMPLE_GATE:
            median, basis = region_medians[rk], "region"
        else:
            c["opportunity"] = "Unrated"
            c["opportunity_basis"] = "none"
            c["opportunity_reason"] = (
                f"Not enough comparable {noun}s in this area yet to price it fairly."
            )
            out.append(c)
            continue

        place = c["comuna"] if basis == "comuna" else "the area"
        ratio = ppm / median
        drop = c.get("price_drop_pct")
        if drop and drop >= PRICE_DROP_TRIGGER:
            opp = "Strong"
            reason = f"The price dropped {drop}% since it was first listed."
        elif ratio > WATCH_RATIO or not _usable(c):
            opp = "Watch"
            if not _usable(c):
                reason = ("Missing water or power, which you'd need before building."
                          if c["class"] == "parcela"
                          else "Still a project, not move-in ready yet.")
            else:
                reason = (f"Priced about {round((ratio - 1) * 100)}% above the typical "
                          f"{noun} in {place} by price/m².")
        elif ratio <= STRONG_RATIO:
            opp = "Strong"
            if c["class"] == "parcela" and c.get("water") and c.get("power"):
                extra = ", and it has water and power"
            elif c["class"] != "parcela" and c.get("status") == "Built":
                extra = ", and it's move-in ready"
            else:
                extra = ""
            reason = (f"Priced about {round((1 - ratio) * 100)}% below the typical "
                      f"{noun} in {place} by price/m²{extra}.")
        else:
            opp = "Fair"
            reason = f"Priced in line with other {noun}s in {place}."

        c["opportunity"] = opp
        c["opportunity_basis"] = basis
        c["opportunity_reason"] = reason
        out.append(c)
    return out
