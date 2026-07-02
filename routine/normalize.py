"""Normalize any source price into canonical UF, then derive USD and UF/m².

We never trust a source's own currency conversion — we recompute everything
from the raw price and today's mindicador rates.
"""


def to_uf(raw_price, currency, fx):
    if currency == "UF":
        return raw_price
    if currency == "CLP":
        return raw_price / fx["uf_clp"]
    if currency == "USD":
        return raw_price * fx["usd_clp"] / fx["uf_clp"]
    raise ValueError(f"unknown currency: {currency}")


def uf_to_usd(price_uf, fx):
    return price_uf * fx["uf_clp"] / fx["usd_clp"]


def normalize_prices(listing, fx):
    """Return a copy of listing with price_uf, price_usd, price_per_m2_uf set."""
    out = dict(listing)
    price_uf = round(to_uf(listing["raw_price"], listing["currency"], fx))
    out["price_uf"] = price_uf
    out["price_usd"] = round(uf_to_usd(price_uf, fx) / 1000) * 1000
    m2 = listing.get("m2")
    out["price_per_m2_uf"] = round(price_uf / m2, 2) if m2 else None
    return out
