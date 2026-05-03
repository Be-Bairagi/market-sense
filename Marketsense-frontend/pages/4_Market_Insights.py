import streamlit as st
import pandas as pd
from datetime import datetime
from data.nifty50 import NIFTY_50_MAP, NIFTY_50_SYMBOLS
from services.dashboard_service import DashboardService
from utils.helpers import (
    format_currency, 
    get_signal_icon, 
    format_date, 
    format_datetime, 
    initialize_ui_context
)
from components.loader import render_loader

# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Market Insights | MarketSense",
    page_icon="🏹",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────
st.markdown(
    """
    <style>
    [data-testid="stMetricValue"] > div {
        white-space: normal !important;
        word-break: break-word !important;
        line-height: 1.2 !important;
        font-size: clamp(1rem, 5vw, 1.5rem) !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialize Global UI
initialize_ui_context()

# ── Sidebar Selection ─────────────────────────────────────────
from utils.helpers import get_default_ticker_index
st.sidebar.header("🔎 Stock Intelligence")
ticker_options = [f"{NIFTY_50_MAP[s]} ({s})" for s in NIFTY_50_SYMBOLS]
default_idx = get_default_ticker_index(NIFTY_50_SYMBOLS)
selected_option = st.sidebar.selectbox("Select Stock:", ticker_options, index=default_idx)
ticker = selected_option.split(" (")[-1].rstrip(")")

st.title("🏹 Market Insights")
st.caption(f"Comprehensive AI intelligence for **{NIFTY_50_MAP.get(ticker, ticker)}**")

# Check experience level
is_beginner = st.session_state.get("user_mode", "💡 Beginner") == "💡 Beginner"

with render_loader("Checking watchlist"):
    watchlist = DashboardService.fetch_watchlist()
    is_in_watchlist = any(item["symbol"] == ticker for item in watchlist) if isinstance(watchlist, list) else False

# Render Watchlist buttons in sidebar now that we have the status
with st.sidebar:
    st.divider()
    if is_in_watchlist:
        if st.button("🗑️ Remove from Watchlist", use_container_width=True, help="Remove this stock from your personalized watchlist."):
            res = DashboardService.remove_from_watchlist(ticker)
            if "error" not in res:
                st.sidebar.success(f"Removed {ticker}")
                st.rerun()
    else:
        if st.button("➕ Add to Watchlist", use_container_width=True, type="primary", help="Add this stock to your watchlist for quick access and tracking."):
            res = DashboardService.add_to_watchlist(ticker)
            if "error" not in res:
                st.sidebar.success(f"Added {ticker}")
                st.rerun()
    st.info("💡 Switch to another stock to see its full intelligence report.")

# Section 1: Company Identity Bar
with render_loader("Fetching profile"):
    profile = DashboardService.fetch_stock_profile(ticker)

if "error" not in profile:
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([1.8, 1.1, 1.3, 1])
        c1.markdown(f"### {profile.get('company_name', ticker)}")
        c1.caption(f"**Symbol:** {ticker} | **Exchange:** {profile.get('exchange', 'NSE')}")
        
        c2.metric("Sector", profile.get("sector", "N/A"), help="Primary business sector of the company.")
        mcap = profile.get("market_cap")
        c3.metric("Market Cap", format_currency(mcap) if mcap else "N/A", help="Total market valuation of the company.")
        c4.metric("Last Sync", format_date(profile.get("last_updated")), help="Last time the system synced this profile data.")
else:
    st.error("Failed to load company profile.")

# Section 2: AI Signal Card
with render_loader(f"Analyzing {ticker}"):
    # Default to xgboost for insights
    prediction = DashboardService.fetch_rich_prediction(ticker, "xgboost")

if "error" not in prediction:
    pred = prediction.get("predictions", {})
    direction = pred.get("direction", "HOLD")
    confidence = pred.get("confidence", 0.0)
    
    with st.container(border=True):
        st.subheader("🎯 AI Signal")
        
        if is_beginner:
            # Simple plain-English summary for beginners
            bg_color = "#e7f3ef" if direction == "BUY" else "#fdeced" if direction == "AVOID" else "#fff8e1"
            text_color = "#065f46" if direction == "BUY" else "#991b1b" if direction == "AVOID" else "#92400e"
            st.markdown(
                f"""<div style="background-color:{bg_color}; color:{text_color}; padding:15px; border-radius:10px; margin-bottom:20px;">
                <strong>AI Summary:</strong> Based on current market data, the system suggests a <strong>{direction}</strong> stance on {ticker}. 
                The model is {confidence:.0%} confident in this signal.
                </div>""", 
                unsafe_allow_html=True
            )

        col_sig, col_metrics = st.columns([1, 2])
        
        with col_sig:
            st.markdown(f"## {get_signal_icon(direction)} {direction}")
            st.write(f"**AI Confidence:** {confidence:.0%}")
            st.progress(float(confidence))
            if pred.get("is_high_confidence"):
                st.success("💎 High Confidence Signal")
        
        with col_metrics:
            m1, m2, m3 = st.columns(3)
            m1.metric("Target (Near)", format_currency(pred.get('target_low', 0)), help="Expected short-term price target if the trend continues.")
            m2.metric("Stop Loss", format_currency(pred.get('stop_loss', 0)), help="Safety exit level to protect your capital if the trade goes against you.")
            m3.metric("Risk Profile", pred.get("risk_level", "MEDIUM"), help="The volatility risk associated with this specific stock right now.")
            
            st.divider()
            drv_col, bear_col = st.columns(2)
            with drv_col:
                st.markdown("**🧠 Key Drivers:**")
                drivers = pred.get("key_drivers", [])
                if drivers:
                    for d in drivers[:3]:
                        st.write(f"- {d}")
                else:
                    st.write("No specific drivers identified.")
            with bear_col:
                bear_case = pred.get("bear_case", "")
                if bear_case:
                    st.warning(f"🐻 **Bear Case:** {bear_case}")
                else:
                    st.info("No immediate downside risks flagged by the AI.")
else:
    st.info(f"💡 No active XGBoost model found for **{ticker}**. Train one in Model Management to see AI signals.")

# Section 3: Latest News & Sentiment
with render_loader("Fetching news"):
    news = DashboardService.fetch_stock_news(ticker, limit=5)

if isinstance(news, list) and news:
    with st.container(border=True):
        st.subheader("📰 Latest News & Sentiment")
        if is_beginner:
            st.caption("How to read: Green dots indicate positive news, Red dots indicate negative or risky news.")
            
        for item in news:
            cols = st.columns([0.08, 0.92])
            cols[0].write(item.get("icon", "⚪"))
            with cols[1]:
                st.markdown(f"**[{item['headline']}]({item['url']})**")
                st.caption(f"{format_datetime(item['published_at'])} | Sentiment: **{item['sentiment'].title()}** ({item['score']:.0%})")
else:
    st.info("No recent news found for this stock.")

# Section 4: Track Record (Expandable)
with st.expander("📊 Historical Track Record", expanded=False):
    if is_beginner:
        st.info("💡 Trust is built on transparency. Here is how our AI performed on this stock in the past.")

    with render_loader("Fetching accuracy"):
        accuracy = DashboardService.fetch_stock_accuracy(ticker)
    
    if "error" not in accuracy and accuracy.get("history"):
        history = accuracy.get("history", [])
        win_rate = accuracy.get("win_rate", 0)
        
        c1, c2 = st.columns([1, 3])
        c1.metric("Win Rate", f"{win_rate}%", help="Percentage of past predictions that correctly hit their target.")
        c1.write(f"Based on {accuracy.get('outcome_samples', 0)} outcomes")
        
        # Simple outcome visual
        outcomes = "".join(["✅" if t.get("outcome") == "WIN" else "❌" for t in history if t.get("outcome")][:10])
        c2.write("**Recent Outcomes:**")
        c2.subheader(outcomes if outcomes else "No outcomes recorded yet")
        c2.caption("Left is most recent")
        
        if st.checkbox("Show detailed history"):
            df_acc = pd.DataFrame(history)
            if not df_acc.empty:
                st.dataframe(
                    df_acc[['date', 'direction', 'confidence', 'outcome', 'model']],
                    use_container_width=True,
                    hide_index=True
                )
    else:
        st.write("No historical accuracy data available for this stock yet.")

st.divider()
st.caption(f"Last updated: {format_datetime(datetime.now())}")
