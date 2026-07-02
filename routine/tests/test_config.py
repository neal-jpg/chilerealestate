from routine import config


def test_regions_are_north_to_south():
    orders = [r["order"] for r in config.REGIONS]
    assert orders == sorted(orders)
    assert [r["code"] for r in config.REGIONS] == ["IX", "XIV", "X"]


def test_source_sets_are_disjoint():
    assert config.SCRAPED_SOURCES.isdisjoint(config.ALERT_SOURCES)


def test_town_region_maps_into_active_regions_only():
    from routine import config
    for town, (region, comuna) in config.TOWN_REGION.items():
        assert region in config.ACTIVE_REGION_CODES
        assert comuna  # canonical name present


def test_publish_config_present():
    from routine import config
    assert config.PAGES_URL.startswith("https://")
    assert config.DEPLOY_ATTEMPTS >= 1
