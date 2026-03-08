import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from app import health_check_ui
from services.dashboard_service import DashboardService

# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Market Pulse | MarketSense",
    page_icon="⏱️",
    layout="wide",
)

# Render offline banner if backend is unreachable
health_check_ui()

st.title("⏱️ Market Pulse")
st.write("A 30-second snapshot of India's macro market conditions.")
st.markdown("---")

# ── Fetch Data ────────────────────────────────────────────────
with st.spinner("Taking the market's pulse..."):
    pulse_data = DashboardService.fetch_market_pulse()

if pulse_data.get("error"):
    st.error(f"❌ Could not load market pulse: {pulse_data['error']}")
    if "404" in pulse_data['error'] or "not found" in pulse_data['error'].lower():
        st.info("💡 Make sure to restart the backend `uvicorn` server so it picks up the new `market_routes.py` file!")
    st.stop()

# ── 2x2 Grid Layout ───────────────────────────────────────────
col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

# --- 1. Index Overview ---
with col1:
    with st.container(border=True):
        st.subheader("📈 Index Overview", help="Tracks the overall performance of the Indian market.")
        indices = pulse_data.get("indices", [])
        if not indices:
            st.info("No index data available yet.")
        else:
            i1, i2 = st.columns(2)
            if len(indices) > 0:
                idx = indices[0]
                color = "normal" if idx["change_pct"] > 0 else "inverse"
                i1.metric(
                    label=f"{idx['name']} ({idx['mood']})",
                    value=f"{idx['value']:,.0f}",
                    delta=f"{idx['change_pct']:.2f}%",
                    delta_color=color
                )
            if len(indices) > 1:
                idx = indices[1]
                color = "normal" if idx["change_pct"] > 0 else "inverse"
                i2.metric(
                    label=f"{idx['name']} ({idx['mood']})",
                    value=f"{idx['value']:,.0f}",
                    delta=f"{idx['change_pct']:.2f}%",
                    delta_color=color
                )

# --- 2. India VIX Interpreter ---
with col2:
    with st.container(border=True):
        st.subheader("📉 Fear Gauge (India VIX)", help="VIX measures expected market volatility. Low numbers indicate calm, high numbers indicate fear.")
        vix = pulse_data.get("vix", {})
        if not vix:
            st.info("VIX data not available.")
        else:
            v_val = vix.get("value", 0)
            v_stat = vix.get("status", "Unknown")
            v_chg = vix.get("change_pct", 0)
            
            st.metric(
                label=f"Current Status: **{v_stat}**",
                value=f"{v_val:.2f}",
                delta=f"{v_chg:.2f}%",
                delta_color="inverse" # VIX going up is usually bad
            )
            # Render a progress bar indicating danger level
            safe_vix = min(max(v_val / 30.0, 0.0), 1.0) # Assume 30 is max fearful
            st.progress(safe_vix, text="Anxiety Level")

# --- 3. Institutional Flow ---
with col3:
    with st.container(border=True):
        st.subheader("🏦 Institutional Flow (Last 5 Days)", help="Shows whether big institutions (FIIs and DIIs) are buying or selling overall.")
        flows = pulse_data.get("fii_dii", {})
        if not flows:
            st.info("Institutional data not available.")
        else:
            fii = flows.get("fii_net", 0)
            dii = flows.get("dii_net", 0)
            
            f1, f2 = st.columns(2)
            f1.metric("FII Net", f"₹{fii:,.0f} Cr", delta="Buying" if fii > 0 else "Selling", delta_color="normal" if fii>0 else "inverse")
            f2.metric("DII Net", f"₹{dii:,.0f} Cr", delta="Buying" if dii > 0 else "Selling", delta_color="normal" if dii>0 else "inverse")
            
            st.write(f"*Last updated: {flows.get('last_updated', 'N/A')}*")

# --- 4. Sector Heatmap ---
with col4:
    with st.container(border=True):
        st.subheader("📊 Sector Heatmap", help="Shows which sectors are performing best/worst based on automated analysis.")
        sectors = pulse_data.get("sectors", [])
        if not sectors:
            st.info("Sector data building...")
        else:
            # We'll build a mini horizontal bar chart using plotly to act as a heatmap
            df = pd.DataFrame(sectors)
            df = df.sort_values(by="change_pct", ascending=True) # Ascending so biggest is at top of horiz bar
            
            fig = go.Figure(go.Bar(
                x=df['change_pct'],
                y=df['name'],
                orientation='h',
                marker=dict(
                    color=df['change_pct'],
                    colorscale=[[0, '#ef4444'], [0.5, '#e2e8f0'], [1, '#10b981']],
                    cmin=-2, cmax=2,
                ),
                text=df.apply(lambda row: f"{row['change_pct']}% ({row['stock_count']} stocks)", axis=1),
                textposition="auto"
            ))
            fig.update_layout(
                margin=dict(l=0, r=0, t=10, b=0),
                height=200,
                xaxis=dict(visible=False),
                yaxis=dict(tickfont=dict(size=10)),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
