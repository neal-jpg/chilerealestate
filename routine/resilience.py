"""Pure decision helpers that let the daily run degrade instead of aborting."""


def resolve_fx(fetch_fn, cached_fx):
    """Live FX if the fetch works; otherwise the cached rates; else re-raise."""
    try:
        return fetch_fn()
    except Exception:
        if cached_fx:
            return cached_fx
        raise


def safe_collect(fn):
    """Run a source collector; on any failure yield [] so the run continues."""
    try:
        return fn()
    except Exception:
        return []


def _active_count(listings):
    return sum(1 for l in listings if l.get("active"))


def should_write(new_listings, prev_listings):
    """Guard against a transient failure blanking the site: skip the write when
    the new data has zero active listings but the previous data had some."""
    return not (_active_count(new_listings) == 0 and _active_count(prev_listings) > 0)
