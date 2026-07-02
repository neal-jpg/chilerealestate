from routine.merge import price_drop_from_snapshots, merge_listings


def test_price_drop_from_snapshots_matches_first_to_current():
    snaps = [
        {"date": "2026-05-20", "price_uf": 9500},
        {"date": "2026-06-22", "price_uf": 8900},
    ]
    assert price_drop_from_snapshots(snaps) == 6  # (9500-8900)/9500 -> 6.3 -> 6
    assert price_drop_from_snapshots([{"date": "x", "price_uf": 100}]) is None
    assert price_drop_from_snapshots(
        [{"date": "a", "price_uf": 100}, {"date": "b", "price_uf": 110}]
    ) is None  # a rise is not a drop


def test_new_listing_gets_first_and_last_seen_and_snapshot():
    listings, snaps = merge_listings(
        existing_listings=[], existing_snapshots={},
        incoming=[{"id": "a", "url": "a", "source": "Yapo", "price_uf": 8900, "region": "IX"}],
        run_date="2026-07-01",
    )
    assert listings[0]["first_seen"] == "2026-07-01"
    assert listings[0]["last_seen"] == "2026-07-01"
    assert listings[0]["active"] is True
    assert snaps["a"] == [{"date": "2026-07-01", "price_uf": 8900}]


def test_price_change_appends_snapshot_and_sets_drop():
    existing = [{"id": "a", "url": "a", "source": "Yapo", "price_uf": 9500,
                 "first_seen": "2026-05-20", "last_seen": "2026-05-20", "active": True, "region": "IX"}]
    snaps0 = {"a": [{"date": "2026-05-20", "price_uf": 9500}]}
    listings, snaps = merge_listings(
        existing_listings=existing, existing_snapshots=snaps0,
        incoming=[{"id": "a", "url": "a", "source": "Yapo", "price_uf": 8900, "region": "IX"}],
        run_date="2026-07-01",
    )
    assert listings[0]["first_seen"] == "2026-05-20"      # preserved
    assert listings[0]["last_seen"] == "2026-07-01"       # advanced
    assert listings[0]["price_uf"] == 8900
    assert len(snaps["a"]) == 2
    assert listings[0]["price_drop_pct"] == 6


def test_unchanged_price_does_not_append_snapshot():
    existing = [{"id": "a", "url": "a", "source": "Yapo", "price_uf": 9500,
                 "first_seen": "2026-05-20", "last_seen": "2026-05-20", "active": True, "region": "IX"}]
    snaps0 = {"a": [{"date": "2026-05-20", "price_uf": 9500}]}
    _, snaps = merge_listings(existing, snaps0,
        incoming=[{"id": "a", "url": "a", "source": "Yapo", "price_uf": 9500, "region": "IX"}],
        run_date="2026-07-01")
    assert len(snaps["a"]) == 1


def test_scraped_listing_expires_after_ttl_alert_listing_lingers():
    existing = [
        {"id": "s", "url": "s", "source": "BuenasParcelas", "price_uf": 2000,
         "first_seen": "2026-06-01", "last_seen": "2026-06-01", "active": True, "region": "X"},
        {"id": "a", "url": "a", "source": "Yapo", "price_uf": 3000,
         "first_seen": "2026-06-01", "last_seen": "2026-06-01", "active": True, "region": "X"},
    ]
    snaps0 = {"s": [{"date": "2026-06-01", "price_uf": 2000}],
              "a": [{"date": "2026-06-01", "price_uf": 3000}]}
    # 30 days later, neither re-seen this run
    listings, _ = merge_listings(existing, snaps0, incoming=[], run_date="2026-07-01")
    by_id = {l["id"]: l for l in listings}
    assert by_id["s"]["active"] is False   # scraped, >10d
    assert by_id["a"]["active"] is True    # alert, <60d


def test_price_drop_rounds_half_up_to_match_the_app():
    # 520 -> 507 is exactly a 2.5% drop; the app's JS Math.round gives 3, and
    # the routine must match so the card pill and the graph never disagree.
    snaps = [{"date": "a", "price_uf": 520}, {"date": "b", "price_uf": 507}]
    assert price_drop_from_snapshots(snaps) == 3


def test_price_rise_appends_snapshot_but_no_drop():
    existing = [{"id": "a", "url": "a", "source": "Yapo", "price_uf": 9500,
                 "first_seen": "2026-05-20", "last_seen": "2026-05-20", "active": True, "region": "IX"}]
    snaps0 = {"a": [{"date": "2026-05-20", "price_uf": 9500}]}
    listings, snaps = merge_listings(existing, snaps0,
        incoming=[{"id": "a", "url": "a", "source": "Yapo", "price_uf": 10000, "region": "IX"}],
        run_date="2026-07-01")
    assert len(snaps["a"]) == 2          # a rise still appends to the series
    assert listings[0]["price_drop_pct"] is None  # ...but shows no drop pill
