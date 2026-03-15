"""
PUREINT Opportunity Engine — Risk & opportunity scoring from real topology.
Fragility and opportunity scores derived from upstream/peer counts.
"""

from typing import Literal

RiskLabel = Literal["High", "Medium", "Low"]


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def compute_fragility(upstream_count: int, peer_count: int) -> float:
    """
    Fragility score 0–100 from real topology.
    - Fewer upstreams = higher fragility (single upstream = very high risk).
    - Fewer peers = lower resilience = higher fragility.
    """
    # Single upstream or zero upstreams (often means tier-1 or missing data) — high fragility
    if upstream_count <= 1:
        upstream_component = 70.0  # base high
        if upstream_count == 0:
            # Tier-1 / no upstream: fragility driven by peer diversity
            upstream_component = 40.0
    elif upstream_count == 2:
        upstream_component = 45.0
    elif upstream_count <= 4:
        upstream_component = 25.0
    else:
        upstream_component = 10.0

    # Peers: fewer = less resilience
    if peer_count <= 2:
        peer_component = 50.0
    elif peer_count <= 5:
        peer_component = 30.0
    elif peer_count <= 10:
        peer_component = 15.0
    else:
        peer_component = 5.0

    raw = (upstream_component * 0.6) + (peer_component * 0.4)
    return round(_clamp(raw, 0.0, 100.0), 1)


def compute_opportunity(fragility_score: float, upstream_count: int, peer_count: int) -> float:
    """
    Opportunity score 0–100: higher where fragility is meaningful and actionable.
    High fragility + low diversity = high opportunity for infrastructure sales.
    """
    # Base: fragility indicates need
    need = fragility_score
    # Actionability: single upstream or very few peers = clear angle
    if upstream_count <= 1 and peer_count <= 5:
        actionability = 1.2
    elif upstream_count <= 2 or peer_count <= 5:
        actionability = 1.0
    else:
        actionability = 0.85
    raw = need * (actionability * 0.95)
    return round(_clamp(raw, 0.0, 100.0), 1)


def get_risk_label(fragility_score: float) -> RiskLabel:
    """Map fragility score to High / Medium / Low."""
    if fragility_score >= 60:
        return "High"
    if fragility_score >= 35:
        return "Medium"
    return "Low"


def score_network(record: dict) -> dict:
    """
    Given a network record with upstream_count and peer_count,
    add fragility_score, opportunity_score, risk_label.
    """
    up = record.get("upstream_count", 0)
    peer = record.get("peer_count", 0)
    fragility = compute_fragility(up, peer)
    opportunity = compute_opportunity(fragility, up, peer)
    label = get_risk_label(fragility)
    return {
        **record,
        "fragility_score": fragility,
        "opportunity_score": opportunity,
        "risk_label": label,
    }


def score_networks(records: list[dict]) -> list[dict]:
    """Score each network record; return list with scores added."""
    return [score_network(r) for r in records]
