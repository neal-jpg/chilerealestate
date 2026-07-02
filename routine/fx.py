"""Daily UF and USD values from mindicador.cl (CLP per unit)."""

import json
import urllib.request

MINDICADOR_URL = "https://mindicador.cl/api"


def parse_mindicador(payload):
    """Turn the mindicador.cl JSON payload into our compact fx dict."""
    return {
        "uf_clp": payload["uf"]["valor"],
        "usd_clp": payload["dolar"]["valor"],
        "date": payload["uf"]["fecha"][:10],
    }


def fetch_fx(url=MINDICADOR_URL):
    """Fetch and parse today's rates. Network shell — not unit-tested."""
    with urllib.request.urlopen(url, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return parse_mindicador(payload)
