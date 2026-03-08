import streamlit as st
from data.nifty50 import NIFTY_50_MAP
from services.dashboard_service import DashboardService

# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Today's Picks | MarketSense",
    page_icon="🏆",
    layout="wide",
)

st.title("🏆 Today's Top Picks")
st.write("AI-curated daily stock picks — scored, filtered, and diversified automatically.")
st.markdown("---")

# ── Controls ──────────────────────────────────────────────────
col_ctrl1, col_ctrl2 = st.columns([3, 1])

with col_ctrl2:
    if st.button("⚡ Run Screener Now", use_container_width=True):
        with st.spinner("Triggering screener run..."):
            result = DashboardService.trigger_screener()
        if result.get("error"):
            st.error(f"❌ {result['error']}")
        else:
            st.success(f"✅ {result.get('message', 'Started!')}")
            st.info("⏳ Screener runs in background. Refresh in ~1 min.")

# ── Fetch & Display Picks ─────────────────────────────────────
data = DashboardService.fetch_todays_picks()

if data.get("error"):
    st.warning(f"⚠️ Could not load picks: {data['error']}")
    st.info("The screener may not have run yet. Click **Run Screener Now** above.")
elif not data.get("picks"):
    st.info("📭 No picks available yet. The screener runs daily at 5:00 PM IST after market close.")
    st.info("You can also manually run it using the button above.")
else:
    st.caption(f"📅 Date: **{data.get('date', 'N/A')}** · {data.get('total_picks', 0)} picks")
    st.write("")

    # ── Render Pick Cards ────
    for pick in data["picks"]:
        rank = pick.get("rank", "?")
        symbol = pick.get("symbol", "")
        name = NIFTY_50_MAP.get(symbol, symbol)
        direction = pick.get("direction", "HOLD")
        confidence = pick.get("confidence", 0)
        composite = pick.get("composite_score", 0)
        sector = pick.get("sector", "")
        risk = pick.get("risk_level", "MEDIUM")
        target_low = pick.get("target_low", 0)
        target_high = pick.get("target_high", 0)
        stop_loss = pick.get("stop_loss", 0)
        drivers = pick.get("key_drivers", [])
        bear_case = pick.get("bear_case", "")

        # Color coding
        colors = {"BUY": "#16a34a", "HOLD": "#ca8a04", "AVOID": "#dc2626"}
        bg_colors = {"BUY": "#f0fdf4", "HOLD": "#fefce8", "AVOID": "#fef2f2"}
        signals = {"BUY": "🟢", "HOLD": "🟡", "AVOID": "🔴"}
        risk_icons = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}

        color = colors.get(direction, "#64748b")
        bg = bg_colors.get(direction, "#f8fafc")
        signal = signals.get(direction, "🟡")

        # Card
        st.markdown(f"""
        <div style="
            background: {bg};
            border-left: 5px solid {color};
            border-radius: 0.75rem;
            padding: 1.25rem 1.5rem;
            margin-bottom: 1rem;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <div>
                    <span style="font-size: 1.5rem; font-weight: 700; color: #1e293b;">
                        #{rank} · {name}
                    </span>
                    <span style="color: #94a3b8; margin-left: 0.5rem;">{symbol}</span>
                    <span style="background: #e2e8f0; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; margin-left: 0.5rem;">
                        {sector}
                    </span>
                </div>
                <div>
                    <span style="font-size: 2rem;">{signal}</span>
                    <span style="font-size: 1.5rem; font-weight: 700; color: {color}; margin-left: 0.5rem;">
                        {direction}
                    </span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Metrics row
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Confidence", f"{confidence:.0%}")
        m2.metric("Score", f"{composite:.3f}")
        m3.metric("Target", f"₹{target_low:,.0f} – ₹{target_high:,.0f}")
        m4.metric("Stop Loss", f"₹{stop_loss:,.0f}")
        m5.metric("Risk", f"{risk_icons.get(risk, '🟡')} {risk}")

        # Drivers + Bear case in an expander
        with st.expander(f"📌 Why {symbol} today?"):
            if drivers:
                for d in drivers:
                    st.markdown(f"- {d}")
            if bear_case:
                st.warning(f"🐻 **Bear Case:** {bear_case}")

        st.write("")

# ── Historical Picks ──────────────────────────────────────────
st.markdown("---")
st.subheader("📜 Historical Picks")

days_back = st.slider("Days to look back:", 1, 30, 7)

if st.button("Load History", use_container_width=True):
    history = DashboardService.fetch_picks_history(days_back)

    if history.get("error"):
        st.warning(f"⚠️ {history['error']}")
    elif not history.get("history"):
        st.info("No historical picks found.")
    else:
        for date_str, picks in history["history"].items():
            st.markdown(f"### 📅 {date_str}")
            for p in picks:
                signal = {"BUY": "🟢", "HOLD": "🟡", "AVOID": "🔴"}.get(p["direction"], "🟡")
                st.markdown(
                    f"**#{p['rank']}** {signal} {p['symbol']} "
                    f"({p['direction']}, {p['confidence']:.0%}) "
                    f"· Score: {p['composite_score']:.3f} · {p['sector']}"
                )
