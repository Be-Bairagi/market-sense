import logging
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from data.nifty50 import NIFTY_50_SYMBOLS, NIFTY_50_MAP
from services.dashboard_service import DashboardService
from components.pulse import render_pulse_skeleton, render_market_pulse_cards
from utils.health import check_backend_health

logger = logging.getLogger(__name__)

# ── Session State ─────────────────────────────────────────────
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
if 'available_models' not in st.session_state:
    st.session_state.available_models = []
if 'models_ticker' not in st.session_state:
    st.session_state.models_ticker = None

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
        _, pulse_toggle_col = st.columns([7, 3])
        with pulse_toggle_col:
            mode_selection = st.segmented_control(
                "View Mode",
                options=["💡 Beginner", "🧠 Expert"],
                default="🧠 Expert",
                label_visibility="collapsed",
                help="Choose 'Beginner' for simple explanations or 'Expert' for technical focus.",
            )
            expert_mode = (mode_selection == "🧠 Expert")
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

# ── Model & Prediction Controls ──────────────────────────────
st.sidebar.header("🤖 Prediction")

if st.session_state.models_ticker != ticker:
    with st.spinner("Loading models..."):
        resp = DashboardService.fetch_available_models(ticker)
    if not isinstance(resp, dict) or resp.get("error"):
        st.session_state.available_models = []
    else:
        st.session_state.available_models = resp.get("models", [])
    st.session_state.models_ticker = ticker

available_models = st.session_state.available_models

if not available_models:
    st.sidebar.warning(
        f"⚠️ No trained models found for **{ticker}**.\n\n"
        "Go to **Model Management** to train one first."
    )
    selected_model = None
    selected_framework = None
    predict_days = 5
else:
    def _model_label(m: dict) -> str:
        fw = m["framework"].upper()
        badge = "Active" if m["is_active"] else "Inactive"
        return f"{m['model_name']}_v{m['version']} ({fw} · {badge})"

    model_labels = [_model_label(m) for m in available_models]
    chosen_label = st.sidebar.selectbox(
        "Select Model:",
        model_labels,
        index=0,
    )
    chosen_idx = model_labels.index(chosen_label)
    selected_model = available_models[chosen_idx]
    selected_framework = selected_model["framework"]

    active_tag = "✅ Active" if selected_model["is_active"] else "⏸ Inactive"
    st.sidebar.write(f"**Framework:** {selected_framework.upper()}")
    st.sidebar.write(f"**Version:** v{selected_model['version']}")
    st.sidebar.write(f"**Status:** {active_tag}")

    if selected_framework == "prophet":
        predict_days = st.sidebar.slider("Prediction Days Ahead:", 1, 30, 10)
    else:
        predict_days = 5

st.sidebar.divider()

fetch_data_btn = st.sidebar.button("📊 Fetch Data", use_container_width=True)
predict_btn = st.sidebar.button(
    "🤖 Run Prediction",
    use_container_width=True,
    disabled=(selected_model is None),
)

with st.sidebar.expander("📖 Jargon Buster (Glossary)"):
    st.markdown("""
    - **VIX**: The 'Fear Gauge'. High = nervous market.
    - **NIFTY 50**: Index of top 50 Indian companies.
    - **RSI**: Measures if a stock is 'oversold' or 'overbought'.
    - **Stop Loss**: A safety net price to sell and limit losses.
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
                    st.dataframe(df, use_container_width=True)

                st.caption(f"🕐 Last updated: {st.session_state.last_updated.strftime('%H:%M:%S')}")
            else:
                st.warning("⚠️ No data returned from backend.")
        except Exception as e:
            logger.exception("Failed to fetch data")
            st.error(f"❌ Failed to fetch data: {e}")

# ── Main Panel: Prediction ────────────────────────────────────
if predict_btn:
    if selected_model is None:
        st.error("⚠️ No model selected.")
    elif selected_framework == "prophet":
        model_name_full = f"{selected_model['model_name']}_v{selected_model['version']}"
        st.subheader(f"🤖 Prophet Prediction — {ticker}")
        try:
            response = DashboardService.fetch_predictions("", "", predict_days, model_name_full)
            if not isinstance(response, dict) or response.get("error"):
                st.error(f"⚠️ Prediction failed: {response.get('error', 'Unknown')}")
            else:
                raw = response.get("predictions", [])
                df_pred = pd.DataFrame(raw)
                if not df_pred.empty:
                    st.line_chart(df_pred.set_index('date')['value'])
                    next_day = df_pred.iloc[-1]
                    st.write(f"**Predicted Price:** ₹{next_day['value']:.2f}")
        except Exception as e:
            st.error(f"⚠️ Error: {e}")
    else:
        model_name_full = f"{selected_model['model_name']}_v{selected_model['version']}"
        with st.spinner(f"Analyzing {ticker}..."):
            result = DashboardService.fetch_predictions("", "", 5, model_name_full)
        if not isinstance(result, dict) or result.get("error"):
            st.error(f"⚠️ Prediction failed: {result.get('error', 'Unknown')}")
        else:
            st.subheader("🎯 AI Prediction Signal")
            pred = result.get("predictions", {})
            direction = pred.get("direction", "HOLD")
            confidence = pred.get("confidence", 0.0)
            
            signals = {"BUY": "🟢", "HOLD": "🟡", "AVOID": "🔴"}
            
            with st.container(border=True):
                st.write(f"### {signals.get(direction, '🟡')} {direction}")
                st.metric("Confidence", f"{confidence:.0%}")
                st.write(f"**Horizon:** {pred.get('horizon', 'short_term')}")
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Target Low", f"₹{pred.get('target_low', 0):,.1f}")
                m2.metric("Target High", f"₹{pred.get('target_high', 0):,.1f}")
                m3.metric("Stop Loss", f"₹{pred.get('stop_loss', 0):,.1f}")
                m4.metric("Risk", pred.get("risk_level", "MEDIUM"))

                if pred.get("key_drivers"):
                    st.write("**Key Drivers:**")
                    for driver in pred["key_drivers"]:
                        st.write(f"- {driver}")
                
                if pred.get("bear_case"):
                    st.warning(f"🐻 **Bear Case:** {pred['bear_case']}")

if not fetch_data_btn and not predict_btn:
    st.info("ℹ️ Select a stock and click **Fetch Data** or **Run Prediction** to begin.")
