import logging

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from data.nifty50 import NIFTY_50_SYMBOLS, NIFTY_50_MAP
from services.dashboard_service import DashboardService

logger = logging.getLogger(__name__)


# ── Session State ─────────────────────────────────────────────
if 'last_updated' not in st.session_state:
    st.session_state.last_updated = None
if 'current_data' not in st.session_state:
    st.session_state.current_data = None
if 'current_ticker' not in st.session_state:
    st.session_state.current_ticker = None

# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="MarketSense Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("📊 MarketSense Dashboard")

# ── Sidebar Controls ──────────────────────────────────────────
st.sidebar.header("🔎 Stock Selection")

# NIFTY 50 tickers with names
ticker_options = [f"{s} — {NIFTY_50_MAP[s]}" for s in NIFTY_50_SYMBOLS]
selected_option = st.sidebar.selectbox(
    "Select Stock:", ticker_options, index=0
)
ticker = selected_option.split(" — ")[0]  # Extract symbol

# Comparison multi-select
compare_tickers = st.sidebar.multiselect(
    "Compare Stocks (optional):",
    NIFTY_50_SYMBOLS,
    default=[]
)

# Period & interval
period = st.sidebar.selectbox(
    "Historical Data Period:", ["7d", "30d", "90d", "180d", "1y"], index=1
)
interval = st.sidebar.selectbox(
    "Interval:", ["1d", "1h", "1wk", "1mo"], index=0
)

st.sidebar.markdown("---")

# ── Model & Prediction Controls ──────────────────────────────
st.sidebar.header("🤖 Prediction")

model_type = st.sidebar.selectbox(
    "Model Type:", ["XGBoost", "Prophet"], index=0
)

if model_type == "Prophet":
    predict_days = st.sidebar.slider("Prediction Days Ahead:", 1, 30, 10)
else:
    predict_days = 5  # XGBoost uses fixed 5-day horizon

st.sidebar.markdown("---")

# Action buttons
fetch_data_btn = st.sidebar.button("📊 Fetch Data", use_container_width=True)
predict_btn = st.sidebar.button("🤖 Run Prediction", use_container_width=True)

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

                # ── Single stock: candlestick + volume ────
                df = all_data[ticker]
                name = NIFTY_50_MAP.get(ticker, ticker)
                st.subheader(f"📈 {name} ({ticker})")

                if all(col in df.columns for col in ['Open', 'High', 'Low', 'Close']):
                    fig = go.Figure(data=[
                        go.Candlestick(
                            x=df['Date'],
                            open=df['Open'], high=df['High'],
                            low=df['Low'], close=df['Close'],
                            name='OHLC',
                            increasing_line_color='#26a69a',
                            decreasing_line_color='#ef5350'
                        )
                    ])
                    fig.update_layout(
                        xaxis_title="Date", yaxis_title="Price (₹)",
                        template="plotly_white",
                        xaxis_rangeslider_visible=False,
                        height=420, hovermode="x unified"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                if 'Volume' in df.columns:
                    fig_vol = go.Figure(data=[
                        go.Bar(
                            x=df['Date'], y=df['Volume'],
                            name='Volume',
                            marker_color='rgba(100, 149, 237, 0.6)'
                        )
                    ])
                    fig_vol.update_layout(
                        xaxis_title="Date", yaxis_title="Volume",
                        template="plotly_white", height=220,
                        hovermode="x unified"
                    )
                    st.plotly_chart(fig_vol, use_container_width=True)

                # ── Comparison chart (if multiple) ────
                if len(tickers_to_fetch) > 1:
                    st.subheader("📊 Price Comparison")
                    fig_cmp = go.Figure()
                    colors = ['#2563eb', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#ec4899']
                    for i, t in enumerate(tickers_to_fetch):
                        if t in all_data and 'Close' in all_data[t].columns:
                            fig_cmp.add_trace(go.Scatter(
                                x=all_data[t]['Date'], y=all_data[t]['Close'],
                                mode='lines', name=t,
                                line=dict(color=colors[i % len(colors)], width=2)
                            ))
                    fig_cmp.update_layout(
                        yaxis_title="Price (₹)", template="plotly_white", height=350
                    )
                    st.plotly_chart(fig_cmp, use_container_width=True)

                # Data table
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
    if model_type == "XGBoost":
        # ── XGBoost: Rich Prediction with Signal Card ────
        with st.spinner(f"Getting AI prediction for {ticker}..."):
            result = DashboardService.fetch_rich_prediction(ticker, "xgboost")

        if result.get("error"):
            error_msg = result["error"]
            if "No active model" in str(error_msg):
                st.error("🤖 No trained XGBoost model found for this stock.")
                st.info("Go to **Model Management** → Select XGBoost → Train the model first.")
            else:
                st.error(f"⚠️ Prediction failed: {error_msg}")
        else:
            st.subheader("🎯 AI Prediction Signal")

            # ── Direction signal ────
            direction = result.get("direction", "HOLD")
            confidence = result.get("confidence", 0.0)

            signal_config = {
                "BUY":  {"emoji": "🟢", "color": "#16a34a", "bg": "#f0fdf4"},
                "HOLD": {"emoji": "🟡", "color": "#ca8a04", "bg": "#fefce8"},
                "AVOID": {"emoji": "🔴", "color": "#dc2626", "bg": "#fef2f2"},
            }
            cfg = signal_config.get(direction, signal_config["HOLD"])

            # Signal card
            st.markdown(f"""
            <div style="
                background: {cfg['bg']};
                border-left: 5px solid {cfg['color']};
                border-radius: 0.75rem;
                padding: 1.5rem;
                margin-bottom: 1rem;
            ">
                <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
                    <span style="font-size: 3rem;">{cfg['emoji']}</span>
                    <div>
                        <div style="font-size: 2rem; font-weight: 700; color: {cfg['color']};">
                            {direction}
                        </div>
                        <div style="color: #64748b; font-size: 0.9rem;">
                            {result.get('horizon', 'short_term')} · Confidence: {confidence:.0%}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Confidence bar
            st.progress(min(confidence, 1.0))

            # ── Price targets ────
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("🎯 Target Low", f"₹{result.get('target_low', 0):,.1f}")
            col2.metric("🎯 Target High", f"₹{result.get('target_high', 0):,.1f}")
            col3.metric("🛑 Stop Loss", f"₹{result.get('stop_loss', 0):,.1f}")

            risk = result.get("risk_level", "MEDIUM")
            risk_colors = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}
            col4.metric("⚡ Risk Level", f"{risk_colors.get(risk, '🟡')} {risk}")

            # ── Key Drivers ────
            key_drivers = result.get("key_drivers", [])
            if key_drivers:
                st.markdown("### 📌 Key Drivers")
                for driver in key_drivers:
                    st.markdown(f"- {driver}")

            # ── Bear Case ────
            bear_case = result.get("bear_case", "")
            if bear_case:
                st.warning(f"🐻 **Bear Case:** {bear_case}")

            # ── Model info ────
            with st.expander("ℹ️ Model Details"):
                st.write(f"**Model:** {result.get('model_name', 'N/A')}")
                st.write(f"**Version:** {result.get('model_version', 'N/A')}")
                st.write(f"**Predicted at:** {result.get('predicted_at', 'N/A')}")
                st.write(f"**Valid until:** {result.get('valid_until', 'N/A')}")
                metrics = result.get("metrics", {})
                if metrics:
                    st.write(f"**Training Accuracy:** {metrics.get('accuracy', 'N/A')}")

    else:
        # ── Prophet: existing flow ────
        try:
            response = DashboardService.fetch_predictions(model_type, ticker, predict_days)
            if response:
                predictions = response.get("predictions", [])
                df_pred = pd.DataFrame(predictions)

                st.subheader(f"🤖 Prophet Prediction — {ticker}")

                fig = go.Figure()
                if "lower_bound" in df_pred.columns and "upper_bound" in df_pred.columns:
                    fig.add_trace(go.Scatter(
                        x=df_pred["date"].tolist() + df_pred["date"].tolist()[::-1],
                        y=df_pred["upper_bound"].tolist() + df_pred["lower_bound"].tolist()[::-1],
                        fill="toself",
                        fillcolor="rgba(37, 99, 235, 0.15)",
                        line=dict(color="rgba(37, 99, 235, 0)"),
                        name="Confidence Interval",
                    ))

                fig.add_trace(go.Scatter(
                    x=df_pred["date"], y=df_pred["value"],
                    mode="lines", name="Predicted",
                    line=dict(color="#2563eb", width=2, dash="dot"),
                ))
                fig.update_layout(
                    yaxis_title="Price (₹)", template="plotly_white",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )
                st.plotly_chart(fig, use_container_width=True)

                next_day = df_pred.iloc[-1]
                st.markdown(
                    f"**Next Predicted Closing Price:** ₹{next_day['value']:.2f} "
                    f"(Range: ₹{next_day['lower_bound']:.2f} – ₹{next_day['upper_bound']:.2f})"
                )
            else:
                st.error("❌ No predictions returned.")
        except Exception as e:
            error_msg = str(e)
            if "No active model found" in error_msg:
                st.error("🤖 No trained Prophet model found. Train one in **Model Management** first.")
            else:
                st.error(f"⚠️ Error: {e}")


# ── Empty state ───────────────────────────────────────────────
if not fetch_data_btn and not predict_btn:
    st.info("ℹ️ Select a stock from the sidebar and click **Fetch Data** or **Run Prediction** to begin.")
