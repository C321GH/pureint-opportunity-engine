"""
PUREINT Opportunity Engine
Convert public network topology into qualified infrastructure opportunities.
"""

import streamlit as st
import pandas as pd

from data_fetch import fetch_networks
from risk_engine import score_networks
from ai_engine import generate_infrastructure_insight, generate_commercial_angle, generate_conversation_starter
from ui_components import (
    render_kpi_cards,
    chart_fragility_by_network,
    chart_peer_vs_upstream,
    chart_opportunity_pipeline,
    chart_resilience_scatter,
    render_detail_panel,
)

# Page config: dark, wide, title
st.set_page_config(
    page_title="PUREINT Opportunity Engine",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Dark enterprise theme
st.markdown("""
<style>
    /* Base */
    .stApp { background: linear-gradient(180deg, #0d1117 0%, #161b22 50%, #0d1117 100%); }
    [data-testid="stHeader"] { background: rgba(13,17,23,0.95); border-bottom: 1px solid #30363d; }
    /* Cards */
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] { color: #e6edf3 !important; }
    div[data-testid="stMetric"] { background: rgba(22,27,34,0.9); border: 1px solid #30363d; border-radius: 8px; padding: 1rem; }
    /* Sidebar */
    [data-testid="stSidebar"] { background: #0d1117; }
    /* Expander / containers */
    .stExpander { border: 1px solid #30363d; border-radius: 6px; }
    /* Tables */
    [data-testid="stDataFrame"] { border: 1px solid #30363d; border-radius: 6px; }
    /* Buttons */
    .stButton > button { background: #238636 !important; color: #fff !important; border: 1px solid #2ea043 !important; border-radius: 6px; }
    .stButton > button:hover { background: #2ea043 !important; border-color: #3fb950 !important; }
    /* Info / success blocks */
    [data-testid="stAlert"] { border: 1px solid #30363d; border-radius: 6px; }
    /* Title area */
    .main-title { font-size: 1.75rem; font-weight: 600; color: #e6edf3; letter-spacing: -0.02em; margin-bottom: 0.25rem; }
    .subtitle { color: #8b949e; font-size: 0.95rem; margin-bottom: 1.5rem; }
</style>
""", unsafe_allow_html=True)


def main() -> None:
    st.markdown('<p class="main-title">PUREINT Opportunity Engine</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="subtitle">Convert public network topology into qualified infrastructure opportunities</p>',
        unsafe_allow_html=True,
    )

    # Load and score data (cached per session)
    if "networks" not in st.session_state:
        with st.spinner("Fetching network topology..."):
            raw = fetch_networks()
            st.session_state["networks"] = score_networks(raw)
            for n in st.session_state["networks"]:
                if "status" not in n:
                    n["status"] = "New"

    networks = st.session_state["networks"]

    # KPIs
    render_kpi_cards(networks)

    st.markdown("---")

    # Charts row
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(chart_fragility_by_network(networks), use_container_width=True)
        st.plotly_chart(chart_peer_vs_upstream(networks), use_container_width=True)
    with c2:
        st.plotly_chart(chart_opportunity_pipeline(networks), use_container_width=True)
        st.plotly_chart(chart_resilience_scatter(networks), use_container_width=True)

    st.markdown("---")
    st.markdown("**Network opportunities** — Select a row to view intelligence and assign to sales.")

    # Main table
    df = pd.DataFrame([
        {
            "Network": n.get("name", ""),
            "ASN": n.get("asn", ""),
            "Country": n.get("country", ""),
            "Upstreams": n.get("upstream_count", 0),
            "Peers": n.get("peer_count", 0),
            "Fragility Score": round(n.get("fragility_score", 0), 1),
            "Opportunity Score": round(n.get("opportunity_score", 0), 1),
            "Status": n.get("status", "New"),
        }
        for n in networks
    ])

    st.dataframe(df, use_container_width=True, hide_index=True)

    # Row selection for detail panel
    row_choices = [f"{n.get('name', '')} (AS{n.get('asn', '')}) — {n.get('country', '')}" for n in networks]
    chosen = st.selectbox("Select a network for detail", range(len(row_choices)), format_func=lambda i: row_choices[i], key="detail_select")
    selected_index = chosen

    # Detail panel + Assign to Sales
    if selected_index is not None and 0 <= selected_index < len(networks):
        record = networks[selected_index]
        st.markdown("---")

        # Cache AI output per (asn, topology hash) so we don't call OpenAI every rerun
        cache_key_insight = f"insight_{record.get('asn')}_{record.get('upstream_count')}_{record.get('peer_count')}"
        cache_key_angle = f"angle_{record.get('asn')}_{record.get('upstream_count')}_{record.get('peer_count')}"
        cache_key_conv = f"conv_{record.get('asn')}_{record.get('upstream_count')}_{record.get('peer_count')}"
        if cache_key_insight not in st.session_state:
            with st.spinner("Generating infrastructure insight..."):
                st.session_state[cache_key_insight] = generate_infrastructure_insight(record)
        if cache_key_angle not in st.session_state:
            with st.spinner("Generating commercial angle..."):
                st.session_state[cache_key_angle] = generate_commercial_angle(record)
        if cache_key_conv not in st.session_state:
            with st.spinner("Generating conversation starter..."):
                st.session_state[cache_key_conv] = generate_conversation_starter(record)

        insight = st.session_state[cache_key_insight]
        commercial_angle = st.session_state[cache_key_angle]
        conversation_starter = st.session_state[cache_key_conv]
        render_detail_panel(record, insight, commercial_angle, conversation_starter)

        st.markdown("**Sales workflow**")
        if record.get("status") == "Assigned":
            st.success("Lead created and assigned to sales team.")
        else:
            if st.button("Assign to Sales", key="assign_btn"):
                record["status"] = "Assigned"
                st.session_state["networks"] = networks
                st.success("Lead created and assigned to sales team.")
                st.rerun()

    # Refresh data (optional)
    st.sidebar.markdown("**Data**")
    if st.sidebar.button("Refresh network data"):
        st.session_state.pop("networks", None)
        for k in list(st.session_state.keys()):
            if k.startswith("insight_") or k.startswith("angle_") or k.startswith("conv_"):
                st.session_state.pop(k, None)
        st.rerun()


if __name__ == "__main__":
    main()
