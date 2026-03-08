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
        close_price = pick.get("latest_close", 0) # Assumes backend provides this, otherwise 0
        drivers = pick.get("key_drivers", [])
        bear_case = pick.get("bear_case", "")

        # Styling logic
        signals = {"BUY": "🟢", "HOLD": "🟡", "AVOID": "🔴"}
        risk_icons = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}
        
        signal_icon = signals.get(direction, "🟡")
        conf_pct = int(confidence * 100)
        
        # Native Streamlit Card
        with st.container(border=True):
            # Header Row
            hdr1, hdr2 = st.columns([3, 1])
            with hdr1:
                st.subheader(f"#{rank} · {name} ({symbol})")
                st.caption(f"**Sector:** {sector}")
            with hdr2:
                # Use a right-aligned metric-like display for the signal
                signal_color = "green" if direction == "BUY" else "orange" if direction == "HOLD" else "red"
                st.markdown(f"<h3 style='text-align: right; margin-top: 0; color: {signal_color};'>{signal_icon} {direction}</h3>", unsafe_allow_html=True)
            
            # Confidence Row
            st.write(f"**AI Confidence:** {conf_pct}%")
            safe_conf = min(max(float(confidence), 0.0), 1.0)
            st.progress(safe_conf)
            
            st.write("")
            
            # Metrics Grid
            st.markdown("##### Key Levels")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Entry Zone (CMP)", f"₹{close_price:,.1f}" if close_price else "₹---")
            
            target_delta = f"{((target_low/close_price)-1)*100:.1f}%" if close_price else None
            m2.metric("Target (Near)", f"₹{target_low:,.1f}", delta=target_delta, delta_color="normal")
            
            sl_delta = f"{((stop_loss/close_price)-1)*100:.1f}%" if close_price else None
            m3.metric("Stop Loss", f"₹{stop_loss:,.1f}", delta=sl_delta, delta_color="inverse")
            
            m4.metric("Risk Profile", risk, delta=risk_icons.get(risk, ""), delta_color="off")
            
            st.markdown("---")
            
            # Drivers
            st.markdown("##### Key Drivers")
            if not drivers:
                st.write("No specific drivers provided.")
            for d in drivers[:3]:
                st.markdown(f"- {d}")
                
            if bear_case and direction == "BUY":
                st.warning(f"**Bear Case Risk:** {bear_case}")
            
            st.write("")
            
            # Action Button
            col1, col2 = st.columns([4, 1])
            with col2:
                if st.button(f"Analyze {symbol} ↗", key=f"btn_analyze_{symbol}", use_container_width=True):
                    st.session_state["selected_ticker"] = symbol
                    st.info("Full analysis page coming soon!")
        
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
