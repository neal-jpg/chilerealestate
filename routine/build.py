"""Compose the routine's core into contract-shaped output, then (in main) do IO.

build() is pure: raw listings + prior state + fx -> the four listing-side data
files' contents. main() is the only place that touches the network and disk.
"""

import json
import os

from . import config
from .normalize import normalize_prices
from .scoring import score_listings
from .yield_bands import apply_yield_bands
from .merge import merge_listings
from .fx import fetch_fx

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
LISTING_FIELDS = [
    "id", "url", "title", "source", "region", "comuna", "class", "type",
    "status", "price_uf", "price_usd", "m2", "price_per_m2_uf", "water",
    "power", "access", "image_url", "yield_band", "opportunity",
    "opportunity_basis", "opportunity_reason", "price_drop_pct", "first_seen", "last_seen", "active",
]


def _project(listing):
    """Keep only contract fields (drop raw_price/currency and any scratch keys)."""
    out = {k: listing.get(k) for k in LISTING_FIELDS}
    out["id"] = listing["url"]
    return out


def build(raw_listings, existing_listings, existing_snapshots, fx, run_date):
    normalized = []
    for raw in raw_listings:
        n = normalize_prices(raw, fx)
        n["id"] = raw["url"]
        normalized.append(n)

    merged, snapshots = merge_listings(existing_listings, existing_snapshots,
                                       normalized, run_date)
    scored = score_listings(merged)
    banded = apply_yield_bands(scored, config.YIELD_BANDS)
    listings = [_project(l) for l in banded]

    active_by_region = {}
    for l in listings:
        if l["active"]:
            active_by_region[l["region"]] = active_by_region.get(l["region"], 0) + 1
    thin = [r["code"] for r in config.REGIONS
            if active_by_region.get(r["code"], 0) < config.THIN_THRESHOLD]

    meta = {"build_date": run_date, "regions": config.REGIONS, "thin_coverage": thin}
    return {"listings": listings, "snapshots": snapshots, "fx": fx, "meta": meta}


def collect_raw(bp_listings, alert_listings):
    """Merge raw listings from all sources, deduped by url (alert wins on a tie
    since alert data is richer). Pure — callers pass in each source's output."""
    by_url = {}
    for r in bp_listings:
        by_url[r["url"]] = r
    for r in alert_listings:  # applied second so alert overrides on duplicate url
        by_url[r["url"]] = r
    return list(by_url.values())


def _load(name, default):
    path = os.path.join(DATA_DIR, name)
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save(name, value):
    path = os.path.join(DATA_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)


def main(run_date, alert_csv_url=None, model_call=None):
    """Wire real IO: fetch fx, scrape BuenasParcelas, extract alerts (if wired),
    run build, write the four listing-side files + advance the alert watermark.

    alert_csv_url / model_call are None until the Make->Sheet pipeline and the
    cloud routine's Claude are wired (Plan 4); alerts are simply skipped until then.
    """
    from .sources import buenasparcelas, alerts
    from . import state as state_mod

    state_path = os.path.join(DATA_DIR, "state.json")
    st = state_mod.load_state(state_path)

    fx = fetch_fx()
    bp_listings = buenasparcelas.collect(config.TOWN_REGION)

    alert_listings = []
    if alert_csv_url and model_call:
        import urllib.request
        with urllib.request.urlopen(alert_csv_url, timeout=40) as resp:
            csv_text = resp.read().decode("utf-8", errors="replace")
        alert_listings, st["alert_watermark"] = alerts.collect_alerts(
            csv_text, st["alert_watermark"], model_call)

    raw_listings = collect_raw(bp_listings, alert_listings)
    existing_listings = _load("listings.json", [])
    existing_snapshots = _load("snapshots.json", {})

    result = build(raw_listings, existing_listings, existing_snapshots, fx, run_date)
    _save("listings.json", result["listings"])
    _save("snapshots.json", result["snapshots"])
    _save("fx.json", result["fx"])
    _save("meta.json", result["meta"])
    state_mod.save_state(state_path, st)
    return result


if __name__ == "__main__":
    from datetime import date
    main(run_date=date.today().isoformat())
