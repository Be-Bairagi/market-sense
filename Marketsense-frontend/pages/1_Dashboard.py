import logging
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from data.nifty50 import NIFTY_50_SYMBOLS, NIFTY_50_MAP
from services.dashboard_service import DashboardService
from components.pulse import render_pulse_skeleton, render_market_pulse_cards
from utils.helpers import format_time, format_date, format_datetime, initialize_ui_context
from utils.health import check_backend_health

logger = logging.getLogger(__name__)

# ── Session State ─────────────────────────────────────────────
# Initialize Global UI
initialize_ui_context()

if 'last_updated' not in st.session_state:
    st.session_state.last_updated = None
if 'current_data' not in st.session_state:
    st.session_state.current_data = None
if 'current_ticker' not in st.session_state:
    st.session_state.current_ticker = None
if 'show_market_pulse' not in st.session_state:
    st.session_state.show_market_pulse = False
if 'pulse_data' not in st.session_state:
    st.session_state.pulse_data = None

# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="MarketSense Dashboard",
    page_icon="📊",
    layout="wide",
)

# Silent health check for Dashboard
if "health_check_done" not in st.session_state:
    healthy, health_data = check_backend_health()
    st.session_state["backend_healthy"] = healthy
    st.session_state["health_data"] = health_data
    st.session_state["health_check_done"] = True

st.title("📊 MarketSense Dashboard")

# ── Market Pulse Header with View Button ─────────────────────────────
pulse_header_col1, pulse_header_col2 = st.columns([5, 1])
with pulse_header_col1:
    st.header("⏱️ Market Pulse")
with pulse_header_col2:
    if st.button(
        "View" if not st.session_state.show_market_pulse else "Hide",
        key="toggle_pulse",
        type="primary" if not st.session_state.show_market_pulse else "secondary",
        use_container_width=True,
    ):
        st.session_state.show_market_pulse = not st.session_state.show_market_pulse
        st.rerun()

# ── Market Pulse Body (Open/Close controlled by session state) ───────
if st.session_state.show_market_pulse:
    with st.expander("Macro Snapshot Details", expanded=True):
        market_pulse_desc = """
        **Is the market "friend or foe" today?** We analyze core Indian indices and market volatility
        to give you a 30-second snapshot of the current macro climate.
        """
        expert_mode = (st.session_state.get("user_mode", "💡 Beginner") == "🧠 Expert")
        if not expert_mode:
            st.markdown(market_pulse_desc)

        CARD_HEIGHT = 250 if expert_mode else 380

        if st.session_state.pulse_data is None:
            render_pulse_skeleton(CARD_HEIGHT)
            st.session_state.pulse_data = DashboardService.fetch_market_pulse()
            st.rerun()
        else:
            if st.session_state.pulse_data.get("error"):
                st.error(
                    f"❌ Could not load market pulse: {st.session_state.pulse_data['error']}"
                )
                if st.button("🔄 Retry", key="retry_pulse"):
                    st.session_state.pulse_data = None
                    st.rerun()
            else:
                render_market_pulse_cards(
                    st.session_state.pulse_data, not expert_mode, CARD_HEIGHT
                )
                if st.button("🔄 Refresh Pulse Data", key="refresh_pulse"):
                    st.session_state.pulse_data = None
                    st.rerun()

st.divider()

# ── Sidebar Controls ──────────────────────────────────────────
# Stock Selection is local to this page

st.sidebar.header("🔎 Stock Selection")
ticker_options = [f"{NIFTY_50_MAP[s]} ({s})" for s in NIFTY_50_SYMBOLS]
selected_option = st.sidebar.selectbox("Select Stock:", ticker_options, index=0)
ticker = selected_option.split(" (")[-1].rstrip(")")

compare_options = [f"{NIFTY_50_MAP[s]} ({s})" for s in NIFTY_50_SYMBOLS]
selected_compares = st.sidebar.multiselect(
    "Compare Stocks (optional):",
    compare_options,
    default=[],
)
compare_tickers = [opt.split(" (")[-1].rstrip(")") for opt in selected_compares]

period = st.sidebar.selectbox(
    "Historical Data Period:", ["7d", "30d", "90d", "180d", "1y"], index=1
)
interval = st.sidebar.selectbox(
    "Interval:", ["1d", "1h", "1wk", "1mo"], index=0
)

st.sidebar.divider()

fetch_data_btn = st.sidebar.button("📊 Fetch Data", use_container_width=True)

with st.sidebar.expander("📖 Hints"):
    st.markdown("""
    - **India VIX**: The 'Fear Gauge'. High values (>20) suggest market fear/volatility.
    - **NIFTY 50**: Benchmark index representing top 50 companies on the NSE.
    - **SENSEX**: Benchmark index representing top 30 companies on the BSE.
    - **OHLC**: Shorthand for Open, High, Low, and Close prices shown in the candlestick chart.
    - **Volume**: The total number of shares traded during the selected interval.
    """)

# ── Main Panel: Chart ─────────────────────────────────────────
if fetch_data_btn:
    with st.spinner(f"Loading {ticker} data..."):
        try:
            tickers_to_fetch = [ticker] + [t for t in compare_tickers if t != ticker]
            all_data = {}
            for t in tickers_to_fetch:
                response = DashboardService.fetch_stock_data(t, period, interval)
                if response.get("data"):
                    all_data[t] = pd.DataFrame(response.get("data", []))

            if all_data:
                st.session_state.current_data = all_data
                st.session_state.current_ticker = ticker
                st.session_state.last_updated = pd.Timestamp.now()
                
                # Convert Date columns to datetime objects for better charting
                for t in all_data:
                    all_data[t]['Date'] = pd.to_datetime(all_data[t]['Date'])

                df = all_data[ticker]
                name = NIFTY_50_MAP.get(ticker, ticker)
                st.subheader(f"📈 {name}")

                if all(col in df.columns for col in ['Open', 'High', 'Low', 'Close']):
                    fig = go.Figure(data=[
                        go.Candlestick(
                            x=df['Date'],
                            open=df['Open'], high=df['High'],
                            low=df['Low'], close=df['Close'],
                            name='OHLC',
                        )
                    ])
                    # Simplify chart layout to fit Streamlit's look
                    fig.update_layout(
                        xaxis_rangeslider_visible=False,
                        height=420,
                        margin=dict(l=0, r=0, t=20, b=0)
                    )
                    st.plotly_chart(fig, use_container_width=True)

                if 'Volume' in df.columns:
                    st.write("**Volume**")
                    st.bar_chart(df.set_index('Date')['Volume'])

                if len(tickers_to_fetch) > 1:
                    st.subheader("📊 Price Comparison")
                    cmp_df = pd.DataFrame()
                    for t in tickers_to_fetch:
                        if t in all_data and 'Close' in all_data[t].columns:
                            t_df = all_data[t][['Date', 'Close']].copy()
                            t_df.columns = ['Date', NIFTY_50_MAP.get(t, t)]
                            if cmp_df.empty:
                                cmp_df = t_df
                            else:
                                cmp_df = pd.merge(cmp_df, t_df, on='Date', how='outer')
                    st.line_chart(cmp_df.set_index('Date'))

                with st.expander(f"📋 View {ticker} raw data"):
                    # Sort by Date descending for the raw table view
                    df_view = df.sort_values(by="Date", ascending=False).copy()
                    df_view["Date"] = df_view["Date"].apply(lambda x: format_date(x))
                    st.dataframe(df_view, use_container_width=True, hide_index=True)

                st.caption(f"🕐 Last updated: {format_datetime(st.session_state.last_updated)}")
            else:
                st.warning("⚠️ No data returned from backend.")
        except Exception as e:
            logger.exception("Failed to fetch data")
            st.error(f"❌ Failed to fetch data: {e}")
else:
    st.info("ℹ️ Select a stock and click **Fetch Data** to visualize market history.")
