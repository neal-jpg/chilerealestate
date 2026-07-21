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
REPO_DIR = os.path.dirname(DATA_DIR)
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


def main(run_date, alert_csv_url=None, model_call=None, publish=False):
    """Daily run: fetch FX (fallback to cached), scrape + extract sources (each
    isolated), build, and — unless it would blank the site — write the four data
    files + advance the alert watermark. With publish=True, commit/push and
    confirm the GitHub Pages deploy.

    alert_csv_url / model_call stay None until the Make->Sheet pipeline and the
    cloud routine's Claude are wired; alerts are skipped until then.
    """
    from .sources import buenasparcelas, alerts
    from . import state as state_mod
    from . import publish as publish_mod
    from .resilience import resolve_fx, safe_collect, should_write

    state_path = os.path.join(DATA_DIR, "state.json")
    st = state_mod.load_state(state_path)

    fx = resolve_fx(fetch_fx, _load("fx.json", None))
    bp_listings = safe_collect(lambda: buenasparcelas.collect(config.TOWN_REGION))

    alert_listings = []
    if alert_csv_url and model_call:
        try:
            csv_text = publish_mod.fetch_text(alert_csv_url)
            alert_listings, st["alert_watermark"] = alerts.collect_alerts(
                csv_text, st["alert_watermark"], model_call)
        except Exception:
            alert_listings = []

    raw_listings = collect_raw(bp_listings, alert_listings)
    existing_listings = _load("listings.json", [])
    existing_snapshots = _load("snapshots.json", {})

    result = build(raw_listings, existing_listings, existing_snapshots, fx, run_date)

    if not should_write(result["listings"], existing_listings):
        print("WARNING: run would blank the site (0 active listings); keeping prior data")
        return {"skipped": True, "listings": result["listings"]}

    _save("listings.json", result["listings"])
    _save("snapshots.json", result["snapshots"])
    _save("fx.json", result["fx"])
    _save("meta.json", result["meta"])
    state_mod.save_state(state_path, st)

    if publish:
        committed = publish_mod.publish(REPO_DIR, f"data: daily refresh {run_date}")
        if committed:
            url = config.PAGES_URL.rstrip("/") + "/data/meta.json"
            ok = publish_mod.verify_deploy(
                run_date,
                check_fn=lambda: publish_mod.build_date_from_meta(publish_mod.fetch_text(url)),
                retrigger_fn=lambda: publish_mod.retrigger(REPO_DIR),
                attempts=config.DEPLOY_ATTEMPTS,
            )
            if not ok:
                print("WARNING: Pages deploy did not confirm after retries")

    return result


if __name__ == "__main__":
    from datetime import date
    from .model import resolve_model_call

    # Extraction prefers the local claude CLI (the cloud routine is already a
    # Claude agent — no API key to manage), falls back to ANTHROPIC_API_KEY,
    # and with neither available main() skips alerts and publishes
    # BuenasParcelas listings exactly as before.
    main(
        run_date=date.today().isoformat(),
        alert_csv_url=config.ALERT_CSV_URL,
        model_call=resolve_model_call(),
        publish=True,
    )
