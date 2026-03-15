"""
PUREINT Opportunity Engine — Network data fetch layer.
Fetches real ASN/topology data from BGPView API with graceful fallback.
"""

import json
import requests
from typing import Any

# Small fixed set of known ASNs for reliable prototype (mix of sizes/regions)
DEFAULT_ASN_LIST = [
    701,      # UUNET / Verizon
    174,      # Cogent
    3356,     # Level3 / Lumen
    2914,     # NTT
    6453,     # Tata
    1299,     # Telia
    6762,     # Telecom Italia
    4826,     # Vocus (AU)
    7545,     # TPG (AU)
    15169,    # Google
    8075,     # Microsoft
]

BGPVIEW_BASE = "https://api.bgpview.io"
REQUEST_TIMEOUT = 10


def _get(url: str) -> dict[str, Any] | None:
    """GET with timeout; returns None on failure."""
    try:
        r = requests.get(url, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def fetch_asn_info(asn: int) -> dict[str, Any] | None:
    """Fetch basic ASN info: name, country, etc."""
    data = _get(f"{BGPVIEW_BASE}/asn/{asn}")
    if not data or "data" not in data:
        return None
    d = data["data"]
    return {
        "asn": d.get("asn"),
        "name": d.get("name") or f"AS{asn}",
        "country_code": d.get("country_code") or "??",
        "description_short": (d.get("description_short") or "")[:200],
    }


def fetch_upstreams(asn: int) -> list[dict[str, Any]]:
    """Fetch upstream ASNs for this ASN."""
    data = _get(f"{BGPVIEW_BASE}/asn/{asn}/upstreams")
    if not data or "data" not in data:
        return []
    return data["data"].get("ipv4_upstreams", []) + data["data"].get("ipv6_upstreams", [])


def fetch_peers(asn: int) -> list[dict[str, Any]]:
    """Fetch peer ASNs for this ASN."""
    data = _get(f"{BGPVIEW_BASE}/asn/{asn}/peers")
    if not data or "data" not in data:
        return []
    return data["data"].get("ipv4_peers", []) + data["data"].get("ipv6_peers", [])


def fetch_network_record(asn: int) -> dict[str, Any] | None:
    """
    Build a single network record: ASN, name, country, upstreams, peers.
    Returns None if base ASN info cannot be fetched.
    """
    info = fetch_asn_info(asn)
    if not info:
        return None
    upstreams = fetch_upstreams(asn)
    peers = fetch_peers(asn)
    # Dedupe by asn
    upstream_asns = list({u.get("asn") for u in upstreams if u.get("asn")})
    peer_asns = list({p.get("asn") for p in peers if p.get("asn")})
    return {
        "asn": info["asn"],
        "name": info["name"],
        "country": info["country_code"],
        "upstream_count": len(upstream_asns),
        "peer_count": len(peer_asns),
        "upstreams": upstream_asns,
        "peers": peer_asns,
    }


def fetch_networks(asn_list: list[int] | None = None) -> list[dict[str, Any]]:
    """
    Fetch network records for the given ASN list (or default list).
    On any API failure, falls back to cached sample so demo always works.
    """
    asns = asn_list or DEFAULT_ASN_LIST
    records: list[dict[str, Any]] = []
    for asn in asns:
        rec = fetch_network_record(asn)
        if rec:
            records.append(rec)
    if not records:
        records = get_cached_sample()
    return records


def get_cached_sample() -> list[dict[str, Any]]:
    """
    Return a small cached sample of network-like records when APIs are down.
    Structure matches fetch_network_record() so risk_engine and UI work unchanged.
    """
    return [
        {"asn": 701, "name": "UUNET / Verizon", "country": "US", "upstream_count": 0, "peer_count": 12, "upstreams": [], "peers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]},
        {"asn": 174, "name": "Cogent Communications", "country": "US", "upstream_count": 0, "peer_count": 8, "upstreams": [], "peers": [1, 2, 3, 4, 5, 6, 7, 8]},
        {"asn": 3356, "name": "Level3 / Lumen", "country": "US", "upstream_count": 1, "peer_count": 6, "upstreams": [701], "peers": [1, 2, 3, 4, 5, 6]},
        {"asn": 2914, "name": "NTT America", "country": "US", "upstream_count": 2, "peer_count": 10, "upstreams": [701, 174], "peers": list(range(1, 11))},
        {"asn": 6453, "name": "Tata Communications", "country": "IN", "upstream_count": 1, "peer_count": 4, "upstreams": [701], "peers": [1, 2, 3, 4]},
        {"asn": 1299, "name": "Telia Carrier", "country": "SE", "upstream_count": 0, "peer_count": 14, "upstreams": [], "peers": list(range(1, 15))},
        {"asn": 6762, "name": "Telecom Italia", "country": "IT", "upstream_count": 2, "peer_count": 7, "upstreams": [1299, 3356], "peers": list(range(1, 8))},
        {"asn": 4826, "name": "Vocus Group", "country": "AU", "upstream_count": 1, "peer_count": 3, "upstreams": [7545], "peers": [1, 2, 3]},
        {"asn": 7545, "name": "TPG Telecom", "country": "AU", "upstream_count": 0, "peer_count": 5, "upstreams": [], "peers": list(range(1, 6))},
        {"asn": 15169, "name": "Google LLC", "country": "US", "upstream_count": 0, "peer_count": 20, "upstreams": [], "peers": list(range(1, 21))},
    ]
