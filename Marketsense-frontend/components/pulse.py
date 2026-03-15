# components/pulse.py
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

PULSE_SKELETON_CSS = """
<style>
@keyframes skeleton-glow {
  0% { background-color: #f8fafc; }
  50% { background-color: #f1f5f9; }
  100% { background-color: #f8fafc; }
}
.pulse-skeleton-card {
  width: 100%;
  border-radius: 0.75rem;
  animation: skeleton-glow 1.5s ease-in-out infinite;
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  padding: 1rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}
.pulse-skeleton-line {
  height: 20px;
  background-color: #e2e8f0;
  border-radius: 4px;
  width: 60%;
  margin-bottom: 0.5rem;
}
.pulse-skeleton-content {
  height: 80px;
  background-color: #e2e8f0;
  border-radius: 6px;
  width: 100%;
}
.pulse-skeleton-small {
  height: 14px;
  background-color: #e2e8f0;
  border-radius: 4px;
  width: 40%;
}
.pulse-skeleton-metric {
  height: 40px;
  background-color: #e2e8f0;
  border-radius: 6px;
  width: 100%;
}
</style>
"""

def render_pulse_skeleton(card_height: int):
    """Renders a grid of skeleton cards to indicate data is loading."""
    st.markdown(PULSE_SKELETON_CSS, unsafe_allow_html=True)
    
    colP1, colP2 = st.columns(2)
    for i, col in enumerate([colP1, colP2]):
        with col:
            # Match the card_height exactly to prevent layout jumping
            with st.container(height=card_height, border=False, key=f"skel_cont_{i}_{card_height}"):
                st.markdown(f"""
                <div class="pulse-skeleton-card" style="height: {card_height-15}px;">
                    <div class="pulse-skeleton-line"></div>
                    <div class="pulse-skeleton-small"></div>
                    <div class="pulse-skeleton-metric"></div>
                    <div class="pulse-skeleton-content"></div>
                    <div class="pulse-skeleton-small" style="width: 80%;"></div>
                </div>
                """, unsafe_allow_html=True)

def render_market_pulse_cards(pulse_data: dict, beginner_mode: bool, card_height: int):
    """Renders the actual Market Pulse cards with the fetched data."""
    # ── Grid Layout ───────────────────────────────────────────
    colP1, colP2 = st.columns(2)
    
    # --- 1. Index Overview ---
    with colP1:
        with st.container(height=card_height, border=True, key=f"index_card_{card_height}"):
            st.subheader("📈 Index Overview", help="Tracks the overall performance of the Indian market.")
            if beginner_mode:
                st.info("The **Index** measures the health of the stock market. **NIFTY 50** represents the top 50 largest companies in India.")
            
            indices = pulse_data.get("indices", [])
            if not indices:
                st.info("No index data available yet.")
            else:
                i1, i2 = st.columns(2)
                for idx, col in zip(indices[:2], [i1, i2]):
                    color = "normal" if idx["change_pct"] > 0 else "inverse"
                    col.metric(
                        label=f"{idx['name']} ({idx['mood']})",
                        value=f"{idx['value']:,.0f}",
                        delta=f"{idx['change_pct']:.2f}%",
                        delta_color=color
                    )
                
                if len(indices) >= 1:
                    mood = indices[0]['mood']
                    mood_colors = {"Bullish": "🟢", "Sideways": "🟡", "Bearish": "🔴"}
                    st.write(f"**Current Mood:** {mood_colors.get(mood, '⚪')} {mood}")
    
    # --- 2. India VIX Interpreter ---
    with colP2:
        with st.container(height=card_height, border=True, key=f"vix_card_{card_height}"):
            st.subheader("📉 Fear Gauge (India VIX)", help="VIX measures expected market volatility. Low numbers indicate calm, high numbers indicate fear.")
            if beginner_mode:
                st.info("**VIX** tracks how nervous investors are. **High VIX** means fear & uncertainty; **Low VIX** means confidence.")
            
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
                safe_vix = min(max(v_val / 30.0, 0.0), 1.0)
                st.progress(safe_vix, text=f"Anxiety Level: {v_stat}")
                
                if v_stat == "Fearful":
                    st.warning("Investors are very nervous. Prices might drop fast.")
                elif v_stat == "Calm":
                    st.success("Investors are confident. A good time for steady growth.")
