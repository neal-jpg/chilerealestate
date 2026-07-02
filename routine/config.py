"""Static configuration for the Chile Property Watch routine.

These are hand-set config constants (regions, per-town yield bands, TTLs),
refreshed manually — not derived from data at runtime.
"""

REGIONS = [
    {"code": "IX", "name": "Araucanía", "order": 1},
    {"code": "XIV", "name": "Los Ríos", "order": 2},
    {"code": "X", "name": "Los Lagos", "order": 3},
]
ACTIVE_REGION_CODES = {r["code"] for r in REGIONS}

# Per-comuna gross-yield bands for turnkey rentals. Hand-set from town-level
# STR data, refreshed quarterly. Comunas with no entry get yield_band=None.
YIELD_BANDS = {
    "Pucón": "~4–8% gross · seasonal",
    "Villarrica": "~4–7% gross · seasonal",
    "Valdivia": "~5–9% gross · seasonal",
    "Puerto Varas": "~4–8% gross · seasonal",
    "Frutillar": "~4–7% gross · seasonal",
    "Puerto Montt": "~5–8% gross",
    "Panguipulli": "~3–6% gross · seasonal",
}

# Source classification drives TTL: scraped sources can be re-checked, so they
# expire fast; alert sources cannot, so they linger.
SCRAPED_SOURCES = {"BuenasParcelas", "SouthernChile"}
ALERT_SOURCES = {"Yapo", "Portal"}
TTL_SCRAPED_DAYS = 10
TTL_ALERT_DAYS = 60

# Opportunity scoring.
SAMPLE_GATE = 5           # min active comps in a (comuna, class) bucket
STRONG_RATIO = 0.85       # <= 85% of median and usable -> Strong
WATCH_RATIO = 1.15        # > 115% of median -> Watch
PRICE_DROP_TRIGGER = 5    # a recorded drop >= 5% -> Strong

# A region with fewer than this many active listings shows a thin-coverage banner.
THIN_THRESHOLD = 3
