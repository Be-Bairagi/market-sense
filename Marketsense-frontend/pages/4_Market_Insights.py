import streamlit as st
import pandas as pd
from datetime import datetime
from data.nifty50 import NIFTY_50_MAP, NIFTY_50_STOCKS
from services.dashboard_service import DashboardService
from utils.helpers import format_currency, get_signal_icon, format_date, format_time

# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Market Insights | MarketSense",
    page_icon="🏆",
    layout="wide",
)

def render_preview_card(symbol):
    """Show a preview before adding to watchlist."""
    with st.spinner(f"Analyzing {symbol}..."):
        prediction = DashboardService.fetch_rich_prediction(symbol)
        if "error" in prediction:
            st.error(f"Could not preview {symbol}: {prediction['error']}")
            return False
        pred_data = prediction.get("predictions", {})
        with st.container(border=True):
            st.markdown(f"#### 🔍 Preview: {symbol}")
            c1, c2, c3 = st.columns(3)
            signal = pred_data.get("direction", "HOLD")
            c1.metric("Current Signal", f"{get_signal_icon(signal)} {signal}")
            c2.metric("AI Confidence", f"{pred_data.get('confidence', 0)}%")
            c3.metric("Risk", pred_data.get("risk_level", "MEDIUM"))
            if st.button(f"➕ Add {symbol} to Watchlist", use_container_width=True):
                res = DashboardService.add_to_watchlist(symbol)
                if "error" in res:
                    st.error(res["error"])
                else:
                    st.success(res.get("message", "Added!"))
                    st.rerun()
    return True

# ── MAIN UI ──────────────────────────────────────────────────
st.title("🏹 Market Insight")

# --- SECTION 1: WATCHLIST ---
st.header("📌 My Watchlist")

# Sidebar for Watchlist management
with st.sidebar:
    st.header("👤 Personalization")
    st.session_state.user_mode = st.radio(
        "Select Your Experience Level:",
        ["💡 Beginner", "🧠 Expert"],
        index=0 if st.session_state.get("user_mode", "💡 Beginner") == "💡 Beginner" else 1,
        help="Beginner mode provides more explanations and tips."
    )
    st.divider()

st.sidebar.header("🔍 Add to Watchlist")
search_symbol = st.sidebar.text_input("Search Ticker (e.g. RELIANCE.NS)", "").upper()
if search_symbol:
    render_preview_card(search_symbol)
    st.sidebar.divider()

# Load Watchlist
with st.spinner("Syncing your watchlist..."):
    watchlist = DashboardService.fetch_watchlist()

if isinstance(watchlist, list) and watchlist:
    alert_count = sum(1 for item in watchlist if item["is_alert"])
    s1, s2, s3 = st.columns(3)
    s1.metric("Total Stocks", len(watchlist))
    s2.metric("Active Alerts", alert_count, delta=alert_count if alert_count > 0 else None, delta_color="inverse")
    s3.metric("Last Sync", format_time(datetime.now()))

    for item in watchlist:
        symbol = item["symbol"]
        is_alert = item["is_alert"]
        drift = item["confidence_drift"]
        with st.container(border=True):
            cols = st.columns([2, 2, 2, 1, 1])
            with cols[0]:
                st.write(f"### {symbol}")
                st.caption(f"Added: {format_date(item['added_at'])}")
            with cols[1]:
                signal = item["current_signal"]
                st.metric("Signal", f"{get_signal_icon(signal)} {signal}", f"{item['current_confidence']}% Conf")
            with cols[2]:
                st.metric("Drift", f"{drift}%", delta=drift, delta_color="normal")
                if is_alert:
                    st.warning("⚠️ High Drift Detected")
            with cols[3]:
                st.metric("Target", format_currency(item["target_high"]))
            with cols[4]:
                st.write("") # Spacer
                if st.button("🗑️", key=f"del_{symbol}", use_container_width=True):
                    res = DashboardService.remove_from_watchlist(symbol)
                    if "error" in res:
                        st.error(res["error"])
                    else:
                        st.success(f"Removed {symbol}")
                        st.rerun()
            if is_alert:
                with st.expander("Why the alert?"):
                    st.write(f"Confidence shifted by **{drift}%** (Baseline: {item['confidence_at_add']}% | Current: {item['current_confidence']}%)")
elif isinstance(watchlist, list):
    st.info("📭 Your watchlist is empty. Search for a stock in the sidebar to add it!")
else:
    st.error("Failed to load watchlist.")

st.markdown("---")

# --- SECTION 2: TODAY'S PICKS ---
st.header("🏆 Today's Top Picks")
st.markdown("AI-ranked opportunities based on 40+ signals.")

col_ctrl1, col_ctrl2 = st.columns([3, 1])
with col_ctrl2:
    if st.button("⚡ Run Screener Now", use_container_width=True):
        with st.spinner("Triggering screener..."):
            result = DashboardService.trigger_screener()
        if result.get("error"):
            st.error(f"❌ {result['error']}")
        else:
            st.success("✅ Started! Refresh in ~1 min.")

# Fetch Picks
data = DashboardService.fetch_todays_picks()
if isinstance(data, dict) and data.get("picks"):
    st.caption(f"📅 Date: **{data.get('date', 'N/A')}** · {data.get('total_picks', 0)} picks")
    for pick in data["picks"]:
        rank = pick.get("rank", "?")
        symbol = pick.get("symbol", "")
        name = NIFTY_50_MAP.get(symbol, symbol)
        direction = pick.get("direction", "HOLD")
        confidence = pick.get("confidence", 0)
        risk = pick.get("risk_level", "MEDIUM")
        target_low = pick.get("target_low", 0)
        close_price = pick.get("latest_close", 0)
        drivers = pick.get("key_drivers", [])
        bear_case = pick.get("bear_case", "")

        signals = {"BUY": "🟢", "HOLD": "🟡", "AVOID": "🔴"}
        risk_icons = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}
        
        with st.container(border=True):
            hdr1, hdr2 = st.columns([3, 1])
            with hdr1:
                st.subheader(f"#{rank} · {name}")
                st.caption(f"**Symbol:** {symbol} · **Sector:** {pick.get('sector', '')}")
            with hdr2:
                # Use native metric for signal
                st.metric("Recommendation", f"{signals.get(direction, '🟡')} {direction}")
            
            st.write(f"**AI Confidence:** {int(confidence * 100)}%")
            st.progress(float(confidence))
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("CMP", format_currency(close_price) if close_price else "---")
            m2.metric("Target (Near)", format_currency(target_low))
            m3.metric("Stop Loss", format_currency(pick.get('stop_loss', 0)))
            m4.metric("Risk Profile", risk, delta=risk_icons.get(risk, ""), delta_color="off")
            
            st.markdown("##### Key Drivers")
            for d in drivers[:2]:
                st.write(f"- {d}")
            if bear_case and direction == "BUY":
                st.warning(f"**Bear Case Risk:** {bear_case}")
else:
    st.info("No picks available yet. The screener runs daily at 5:00 PM IST.")

# Historical Picks
with st.expander("📜 View Historical Picks"):
    days_back = st.slider("Days back:", 1, 30, 7)
    if st.button("Load History"):
        history = DashboardService.fetch_picks_history(days_back)
        if not history.get("error"):
            for date_str, picks in history.get("history", {}).items():
                st.write(f"**📅 {date_str}**")
                for p in picks:
                    s = {"BUY": "🟢", "HOLD": "🟡", "AVOID": "🔴"}.get(p["direction"], "🟡")
                    st.write(f"#{p['rank']} {s} {p['symbol']} ({p['direction']})")
