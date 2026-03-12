import streamlit as st
import pandas as pd
from datetime import datetime

from services.dashboard_service import DashboardService
from utils.helpers import format_currency, get_signal_icon
from data.nifty50 import NIFTY_50_STOCKS

# Page configuration
st.set_page_config(
    page_title="My Watchlist | MarketSense",
    page_icon="📌",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .watchlist-card {
        background-color: #ffffff;
        border: 1px solid #e1e4e8;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        transition: transform 0.2s;
    }
    .watchlist-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .drift-badge {
        font-size: 0.8rem;
        padding: 2px 8px;
        border-radius: 12px;
        font-weight: bold;
    }
    .alert-card {
        border-left: 5px solid #ffc107;
        background-color: #fff9e6;
    }
</style>
""", unsafe_allow_html=True)

def render_preview_card(symbol):
    """Show a preview before adding to watchlist."""
    with st.spinner(f"Analyzing {symbol}..."):
        # We use rich prediction for preview
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

def main():
    st.title("📌 My Watchlist")
    st.markdown("Track your favorite stocks and get alerted on significant AI confidence shifts.")

    # Sidebar: Search & Add
    st.sidebar.header("🔍 Add Stock")
    search_symbol = st.sidebar.text_input("Search Ticker (e.g. RELIANCE.NS)", "").upper()
    
    if search_symbol:
        render_preview_card(search_symbol)
        st.sidebar.divider()

    # Load Watchlist
    with st.spinner("Syncing your watchlist..."):
        watchlist = DashboardService.fetch_watchlist()

    if "error" in watchlist:
        st.error(f"Failed to load watchlist: {watchlist['error']}")
        return

    if not watchlist:
        st.info("📭 Your watchlist is empty. Search for a stock in the sidebar to add it!")
        return

    # Watchlist Stats
    alert_count = sum(1 for item in watchlist if item["is_alert"])
    s1, s2, s3 = st.columns(3)
    s1.metric("Total Stocks", len(watchlist))
    s2.metric("Active Alerts", alert_count, delta=alert_count if alert_count > 0 else None, delta_color="inverse")
    s3.metric("Last Sync", datetime.now().strftime("%H:%M:%S"))

    st.divider()

    # Watchlist Grid
    for item in watchlist:
        symbol = item["symbol"]
        is_alert = item["is_alert"]
        drift = item["confidence_drift"]
        
        # Card Header
        with st.container(border=True):
            cols = st.columns([2, 2, 2, 1, 1, 1])
            
            with cols[0]:
                st.markdown(f"#### {symbol}")
                st.caption(f"Added at: {item['added_at'][:10]}")
            
            with cols[1]:
                signal = item["current_signal"]
                st.markdown(f"**Signal:** {get_signal_icon(signal)} **{signal}**")
                st.write(f"Confidence: **{item['current_confidence']}%**")

            with cols[2]:
                drift_label = f"{'+' if drift > 0 else ''}{drift}%"
                drift_color = "red" if drift <= -10 else "green" if drift >= 10 else "grey"
                st.markdown(f"**Drift:** <span style='color:{drift_color}; font-weight:bold;'>{drift_label}</span>", unsafe_allow_html=True)
                if is_alert:
                    st.warning("⚠️ High Drift Detected")

            with cols[3]:
                st.write(f"**Target:**")
                st.write(format_currency(item["target_high"]))

            with cols[4]:
                if st.button("👁️ Details", key=f"view_{symbol}", use_container_width=True):
                    st.query_params["symbol"] = symbol
                    st.switch_page("pages/3_Stock_Deep_Dive.py")

            with cols[5]:
                if st.button("🗑️", key=f"del_{symbol}", use_container_width=True, help="Remove from watchlist"):
                    res = DashboardService.remove_from_watchlist(symbol)
                    if "error" in res:
                        st.error(res["error"])
                    else:
                        st.success(f"Removed {symbol}")
                        st.rerun()

            if is_alert:
                with st.expander("Why the alert?"):
                    st.write(f"""
                    The AI confidence for **{symbol}** has shifted by **{drift}%** since you added it. 
                    Baseline: {item['confidence_at_add']}% | Current: {item['current_confidence']}%
                    """)
                    st.info("Check the **Stock Deep Dive** page to see the updated key drivers and technical signals.")

    st.sidebar.markdown("---")
    st.sidebar.caption("Shift Alerts trigger when AI confidence changes by 10% or more.")

if __name__ == "__main__":
    main()
