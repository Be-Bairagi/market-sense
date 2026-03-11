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
    """Renders a 2x2 grid of skeleton cards to indicate data is loading."""
    st.markdown(PULSE_SKELETON_CSS, unsafe_allow_html=True)
    
    colP1, colP2 = st.columns(2)
    colP3, colP4 = st.columns(2)
    for i, col in enumerate([colP1, colP2, colP3, colP4]):
        with col:
            # Match the card_height exactly to prevent layout jumping
            with st.container(height=card_height, border=False, key=f"skel_cont_{i}_{card_height}"):
                if i < 3: # First 3 cards (Indices, VIX, Flows)
                    st.markdown(f"""
                    <div class="pulse-skeleton-card" style="height: {card_height-15}px;">
                        <div class="pulse-skeleton-line"></div>
                        <div class="pulse-skeleton-small"></div>
                        <div class="pulse-skeleton-metric"></div>
                        <div class="pulse-skeleton-content"></div>
                        <div class="pulse-skeleton-small" style="width: 80%;"></div>
                    </div>
                    """, unsafe_allow_html=True)
                else: # Sector Card (Grid Skeleton)
                    st.markdown(f"""
                    <div class="pulse-skeleton-card" style="height: {card_height-15}px;">
                        <div class="pulse-skeleton-line"></div>
                        <div class="pulse-skeleton-small" style="margin-bottom: 10px;"></div>
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;">
                            {"".join(['<div style="height: 60px; background-color: #e2e8f0; border-radius: 8px;"></div>' for _ in range(6)])}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

def render_market_pulse_cards(pulse_data: dict, beginner_mode: bool, card_height: int):
    """Renders the actual Market Pulse cards with the fetched data."""
    # ── 2x2 Grid Layout ───────────────────────────────────────────
    colP1, colP2 = st.columns(2)
    colP3, colP4 = st.columns(2)
    
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
                    st.markdown(f"**Current Mood:** {mood_colors.get(mood, '⚪')} {mood}")
    
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
    
    # --- 3. Institutional Flow ---
    with colP3:
        with st.container(height=card_height, border=True, key=f"flow_card_{card_height}"):
            st.subheader("🏦 Institutional Flow", help="Shows whether big institutions (FIIs and DIIs) are buying or selling overall.")
            if beginner_mode:
                st.info("**FII** (Foreign Investors) and **DII** (Mutual Funds, LIC) move the big money. If they are 'Buying', it's a very positive sign.")
            
            flows = pulse_data.get("fii_dii", {})
            if not flows:
                st.info("Institutional data not available.")
            else:
                fii = flows.get("fii_net", 0)
                dii = flows.get("dii_net", 0)
                
                f1, f2 = st.columns(2)
                f1.metric("FII Net", f"₹{fii:,.0f} Cr", delta="Buying" if fii > 0 else "Selling", delta_color="normal" if fii>0 else "inverse")
                f2.metric("DII Net", f"₹{dii:,.0f} Cr", delta="Buying" if dii > 0 else "Selling", delta_color="normal" if dii>0 else "inverse")
                
                st.caption(f"Last updated: {flows.get('last_updated', 'N/A')}")
    
    # --- 4. Sector Performance ---
    with colP4:
        with st.container(height=card_height, border=True, key=f"sector_card_{card_height}"):
            st.subheader("📊 Sector Movement", help="Shows which sectors are performing best/worst based on automated analysis.")
            if beginner_mode:
                st.info("The **Stocks** are grouped into industries (Sectors). See which ones are winning today.")
            
            sectors = pulse_data.get("sectors", [])
            if not sectors:
                st.info("Sector data building...")
            else:
                df = pd.DataFrame(sectors)
                df = df.sort_values(by="change_pct", ascending=False)

                # Render tiles in rows of 2, centred using side spacers (Streamlit-native)
                sector_list = df.to_dict("records")
                for row_start in range(0, len(sector_list), 2):
                    row_items = sector_list[row_start: row_start + 2]
                    # [spacer | tile | tile | spacer] — equal spacers centre the two tiles
                    cols = st.columns([1] + [2] * len(row_items) + [1])
                    for col_idx, sector in enumerate(row_items):
                        change = sector["change_pct"]
                        if change > 0:
                            intensity = min(abs(change) / 2.0, 1.0)
                            bg = f"rgba(34, 197, 94, {0.1 + intensity * 0.4})"
                            fg = "#15803d"
                            sign = "+"
                        elif change < 0:
                            intensity = min(abs(change) / 2.0, 1.0)
                            bg = f"rgba(239, 68, 68, {0.1 + intensity * 0.4})"
                            fg = "#b91c1c"
                            sign = ""
                        else:
                            bg = "#f1f5f9"
                            fg = "#64748b"
                            sign = ""
                        with cols[col_idx + 1]:  # +1 to skip left spacer column
                            st.markdown(
                                f'<div style="background:{bg};border:1px solid {fg}22;'
                                f'border-radius:8px;padding:8px 6px;text-align:center;'
                                f'margin-bottom:6px;">'
                                f'<div style="font-size:0.7rem;font-weight:600;color:rgba(0,0,0,0.7);'
                                f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="{sector["name"]}">'
                                f'{sector["name"]}</div>'
                                f'<div style="font-size:0.85rem;font-weight:800;color:{fg};">'
                                f'{sign}{change}%</div></div>',
                                unsafe_allow_html=True,
                            )
