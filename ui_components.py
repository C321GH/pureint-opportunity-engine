"""
PUREINT Opportunity Engine — Reusable UI components (KPIs, charts, detail panel).
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


# Shared chart layout: dark, minimal grid
CHART_LAYOUT = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(18,22,28,0.8)",
    "font": {"color": "#a0aec0", "size": 11},
    "margin": {"t": 24, "b": 32, "l": 44, "r": 24},
    "xaxis": {"gridcolor": "rgba(160,174,192,0.15)", "zeroline": False},
    "yaxis": {"gridcolor": "rgba(160,174,192,0.15)", "zeroline": False},
    "showlegend": True,
    "legend": {
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "right",
        "x": 1,
        "font": {"size": 10},
    },
}


# ------------------------------------------------
# KPI CARDS
# ------------------------------------------------
def render_kpi_cards(networks: list[dict]) -> None:

    total = len(networks)
    high_fragility = sum(1 for n in networks if n.get("risk_label") == "High")
    assigned = sum(1 for n in networks if n.get("status") == "Assigned")
    avg_frag = sum(n.get("fragility_score", 0) for n in networks) / total if total else 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Networks analyzed", total)

    with col2:
        st.metric("High fragility networks", high_fragility)

    with col3:
        st.metric("Opportunities created", assigned)

    with col4:
        st.metric("Avg fragility score", f"{avg_frag:.1f}")


# ------------------------------------------------
# CHART 1
# ------------------------------------------------
def chart_fragility_by_network(networks: list[dict]) -> go.Figure:

    df = pd.DataFrame([
        {
            "Network": f"{n.get('name','')} (AS{n.get('asn','')})",
            "Fragility": n.get("fragility_score", 0),
        }
        for n in networks
    ])

    df = df.sort_values("Fragility", ascending=True)

    fig = px.bar(
        df,
        x="Fragility",
        y="Network",
        orientation="h",
        color="Fragility",
        color_continuous_scale="Reds",
    )

    fig.update_layout(**CHART_LAYOUT)
    fig.update_coloraxes(showscale=False)

    return fig


# ------------------------------------------------
# CHART 2
# ------------------------------------------------
def chart_peer_vs_upstream(networks: list[dict]) -> go.Figure:

    df = pd.DataFrame([
        {
            "Network": f"AS{n.get('asn','')}",
            "Peers": n.get("peer_count", 0),
            "Upstreams": n.get("upstream_count", 0),
        }
        for n in networks
    ])

    fig = px.scatter(
        df,
        x="Upstreams",
        y="Peers",
        text="Network",
    )

    fig.update_traces(
        textposition="top center",
        marker=dict(line=dict(width=1, color="#4a5568")),
    )

    fig.update_layout(**CHART_LAYOUT, title_text="Peer count vs upstream count")

    return fig


# ------------------------------------------------
# CHART 3
# ------------------------------------------------
def chart_opportunity_pipeline(networks: list[dict]) -> go.Figure:

    risk_order = ["High", "Medium", "Low"]

    counts = {}

    for r in risk_order:
        counts[r] = sum(1 for n in networks if n.get("risk_label") == r)

    df = pd.DataFrame(
        [{"Risk": k, "Count": v} for k, v in counts.items()]
    )

    fig = px.bar(
        df,
        x="Risk",
        y="Count",
        color="Count",
        color_continuous_scale="Viridis",
    )

    fig.update_layout(**CHART_LAYOUT, title_text="Opportunity pipeline by risk")
    fig.update_coloraxes(showscale=False)

    return fig


# ------------------------------------------------
# DETAIL PANEL
# ------------------------------------------------
def render_detail_panel(record: dict, insight: str, commercial_angle: str, conversation_starter: str) -> None:

    st.subheader("Intelligence detail")

    c1, c2 = st.columns(2)

    # LEFT COLUMN
    with c1:

        st.markdown(f"**Network** — {record.get('name','')} (AS{record.get('asn','')})")
        st.markdown(f"**Country** — {record.get('country','')}")
        st.markdown(f"**Upstreams** — {record.get('upstream_count',0)}")
        st.markdown(f"**Peers** — {record.get('peer_count',0)}")
        st.markdown(f"**Fragility score** — {record.get('fragility_score',0):.1f}")
        st.markdown(f"**Opportunity score** — {record.get('opportunity_score',0):.1f}")

    # RIGHT COLUMN
    with c2:

        up = record.get("upstream_count", 0)
        peer = record.get("peer_count", 0)

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=["Upstreams", "Peers"],
                    values=[up, peer],
                    hole=0.5,
                )
            ]
        )

        fig.update_layout(
            title="Topology signal",
            showlegend=True,
            height=220,
        )

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        st.markdown("**Infrastructure insight**")
        st.info(insight)

        st.markdown("**Commercial angle**")
        st.info(commercial_angle)

        st.markdown("**Conversation starter**")
        st.info(conversation_starter)
