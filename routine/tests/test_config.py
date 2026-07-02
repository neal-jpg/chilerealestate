from routine import config


def test_regions_are_north_to_south():
    orders = [r["order"] for r in config.REGIONS]
    assert orders == sorted(orders)
    assert [r["code"] for r in config.REGIONS] == ["IX", "XIV", "X"]


def test_source_sets_are_disjoint():
    assert config.SCRAPED_SOURCES.isdisjoint(config.ALERT_SOURCES)
