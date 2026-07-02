"""Apply hand-set gross-yield bands to turnkey listings (parcelas get none)."""


def apply_yield_bands(listings, bands):
    out = []
    for l in listings:
        c = dict(l)
        if c["class"] == "turnkey":
            c["yield_band"] = bands.get(c["comuna"])
        else:
            c["yield_band"] = None
        out.append(c)
    return out
