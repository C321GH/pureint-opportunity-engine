"""
PUREINT Opportunity Engine — OpenAI-powered infrastructure insight and sales copy.
"""

import os
from typing import Any

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

_client: Any = None


def _get_client() -> Any:
    global _client
    if _client is not None:
        return _client
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or not OpenAI:
        return None
    _client = OpenAI(api_key=api_key)
    return _client


def _fallback_insight(record: dict) -> str:
    """Fallback when OpenAI is unavailable."""
    up = record.get("upstream_count", 0)
    peer = record.get("peer_count", 0)
    fragility = record.get("fragility_score", 0)
    if up <= 1 and peer <= 5:
        return (
            "This network shows limited upstream and peer diversity, which can increase "
            "routing dependency and outage risk. An infrastructure intelligence offering "
            "could help them model alternate paths and quantify resilience."
        )
    if up <= 2:
        return (
            "Moderate upstream diversity reduces single-point-of-failure risk but leaves "
            "room for optimization. Visibility into path performance and failover behavior "
            "would support capacity and resilience planning."
        )
    return (
        "Relatively diverse topology suggests mature peering and upstream strategy. "
        "Opportunities may focus on optimization, cost, or compliance visibility rather than "
        "basic resilience."
    )


def _fallback_commercial_angle(record: dict) -> str:
    """Fallback commercial angle when OpenAI is unavailable."""
    up = record.get("upstream_count", 0)
    peer = record.get("peer_count", 0)
    if up <= 1 and peer <= 5:
        return "Position resilience and diversity assessments; offer path visibility and failover modeling."
    if up <= 2:
        return "Sell visibility into upstream performance and redundancy planning."
    return "Focus on optimization, cost, or compliance dashboards rather than basic resilience."


def _fallback_conversation_starter(record: dict) -> str:
    """Fallback conversation starter when OpenAI is unavailable."""
    name = record.get("name", "your network")
    up = record.get("upstream_count", 0)
    peer = record.get("peer_count", 0)
    return (
        f"We've been looking at public routing data for networks like {name}. "
        f"With {up} upstream(s) and {peer} peers, many teams are now interested in "
        "mapping resilience and failover behavior. Would it be useful to run a quick "
        "topology-based view of your current exposure?"
    )


def generate_infrastructure_insight(record: dict) -> str:
    """
    Use OpenAI to explain infrastructure meaning of this network's topology.
    Passes real metrics; returns fallback text if API key missing or call fails.
    """
    client = _get_client()
    if not client:
        return _fallback_insight(record)

    prompt = (
        "You are an expert in network infrastructure and BGP/routing. In one short paragraph, "
        "explain what the following topology implies for routing resilience and operational risk. "
        "Use plain language suitable for a technical buyer. Do not use bullet points.\n\n"
        f"Network: {record.get('name', 'Unknown')} (AS{record.get('asn', '?')}), "
        f"Country: {record.get('country', '?')}. "
        f"Upstreams: {record.get('upstream_count', 0)}, Peers: {record.get('peer_count', 0)}. "
        f"Fragility score (0-100): {record.get('fragility_score', 0)}."
    )
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        )
        text = (resp.choices[0].message.content or "").strip()
        return text or _fallback_insight(record)
    except Exception:
        return _fallback_insight(record)


def generate_commercial_angle(record: dict) -> str:
    """
    Use OpenAI to generate a recommended commercial angle for this network.
    Fallback if API unavailable.
    """
    client = _get_client()
    if not client:
        return _fallback_commercial_angle(record)
    prompt = (
        "You are a sales strategist for an infrastructure intelligence product. "
        "In one short sentence, state the recommended commercial angle for approaching "
        "this network operator (what to sell and how to frame it). Be specific and actionable. "
        f"Network: {record.get('name', 'Unknown')}. Upstreams: {record.get('upstream_count', 0)}, "
        f"Peers: {record.get('peer_count', 0)}. Fragility score: {record.get('fragility_score', 0)}."
    )
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120,
        )
        text = (resp.choices[0].message.content or "").strip()
        return text or _fallback_commercial_angle(record)
    except Exception:
        return _fallback_commercial_angle(record)


def generate_conversation_starter(record: dict) -> str:
    """
    Use OpenAI to generate a suggested sales conversation starter.
    Based on real topology; fallback if API unavailable.
    """
    client = _get_client()
    if not client:
        return _fallback_conversation_starter(record)

    prompt = (
        "You are a sales engineer for an infrastructure intelligence product. "
        "Write one short, professional paragraph: a suggested opening line for a sales call "
        "with this network operator. Reference their real topology (upstreams, peers) and "
        "frame it as a helpful conversation about resilience or visibility. Do not use bullet points. "
        "Tone: consultative, not pushy.\n\n"
        f"Network: {record.get('name', 'Unknown')} (AS{record.get('asn', '?')}). "
        f"Upstreams: {record.get('upstream_count', 0)}, Peers: {record.get('peer_count', 0)}. "
        f"Fragility score: {record.get('fragility_score', 0)}."
    )
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
        )
        text = (resp.choices[0].message.content or "").strip()
        return text or _fallback_conversation_starter(record)
    except Exception:
        return _fallback_conversation_starter(record)
