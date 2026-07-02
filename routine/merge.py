"""Merge this run's listings into prior state: dedup by url, track first/last
seen, append a price snapshot only when the price changes, and expire stale
listings by source-specific TTL (kept in the dataset but marked inactive so the
app's Saved tab can still reconcile them)."""

from datetime import date

from .config import SCRAPED_SOURCES, TTL_SCRAPED_DAYS, TTL_ALERT_DAYS


def price_drop_from_snapshots(snaps):
    """Percent drop from the first snapshot to the current one, or None.

    Single source of truth for the drop: the app's price-history graph reads the
    same first-vs-last from snapshots, so the card pill and the graph agree. We
    round half-UP with int(x + 0.5) to match the app's JS Math.round exactly
    (Python's built-in round() does banker's rounding and would diverge on a .5%
    boundary, e.g. a 2.5% drop).
    """
    if not snaps or len(snaps) < 2:
        return None
    first, last = snaps[0]["price_uf"], snaps[-1]["price_uf"]
    if last >= first:
        return None
    pct = int((first - last) / first * 100 + 0.5)
    return pct if pct >= 1 else None


def _ttl_days(source):
    return TTL_SCRAPED_DAYS if source in SCRAPED_SOURCES else TTL_ALERT_DAYS


def _days_between(a, b):
    return (date.fromisoformat(b) - date.fromisoformat(a)).days


def merge_listings(existing_listings, existing_snapshots, incoming, run_date):
    """Return (merged_listings, merged_snapshots)."""
    existing_by_id = {l["id"]: dict(l) for l in existing_listings}
    snaps = {k: list(v) for k, v in existing_snapshots.items()}
    seen_ids = set()

    for raw in incoming:
        rid = raw["id"]
        seen_ids.add(rid)
        prior = existing_by_id.get(rid)
        if prior is None:
            merged = dict(raw)
            merged["first_seen"] = run_date
            merged["last_seen"] = run_date
            merged["active"] = True
            snaps[rid] = [{"date": run_date, "price_uf": raw["price_uf"]}]
        else:
            merged = dict(raw)
            merged["first_seen"] = prior["first_seen"]
            merged["last_seen"] = run_date
            merged["active"] = True
            hist = snaps.get(rid, [])
            if not hist or hist[-1]["price_uf"] != raw["price_uf"]:
                hist = hist + [{"date": run_date, "price_uf": raw["price_uf"]}]
            snaps[rid] = hist
        merged["price_drop_pct"] = price_drop_from_snapshots(snaps[rid])
        existing_by_id[rid] = merged

    # Expire anything not seen this run, per source TTL.
    for lid, l in existing_by_id.items():
        if lid in seen_ids:
            continue
        if _days_between(l["last_seen"], run_date) > _ttl_days(l["source"]):
            l["active"] = False

    return list(existing_by_id.values()), snaps
