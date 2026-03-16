import logging
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from data.nifty50 import NIFTY_50_SYMBOLS, NIFTY_50_MAP
from services.dashboard_service import DashboardService
from utils.helpers import format_currency, initialize_ui_context

logger = logging.getLogger(__name__)

# ── Session State ─────────────────────────────────────────────
# Initialize Global UI
initialize_ui_context()

if 'available_models' not in st.session_state:
    st.session_state.available_models = []
if 'models_ticker' not in st.session_state:
    st.session_state.models_ticker = None

# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Market Predictions | MarketSense",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 AI Market Predictions")
st.write("Generate and analyze AI signals for your selected stocks.")

st.divider()

# Sidebar logic handled by initialize_ui_context

st.sidebar.header("🔎 Stock Selection")
ticker_options = [f"{NIFTY_50_MAP[s]} ({s})" for s in NIFTY_50_SYMBOLS]
selected_option = st.sidebar.selectbox("Select Stock:", ticker_options, index=0)
ticker = selected_option.split(" (")[-1].rstrip(")")

st.sidebar.divider()

# ── Model & Prediction Controls ──────────────────────────────
st.sidebar.header("🤖 Prediction")

if st.session_state.models_ticker != ticker:
    with st.spinner("Loading models..."):
        resp = DashboardService.fetch_available_models(ticker)
    if not isinstance(resp, dict) or resp.get("error"):
        st.session_state.available_models = []
    else:
        # Filter to SHOW ONLY ACTIVE MODELS as requested
        all_m = resp.get("models", [])
        st.session_state.available_models = [m for m in all_m if m.get("is_active")]
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

predict_btn = st.sidebar.button(
    "🤖 Run Prediction",
    use_container_width=True,
    disabled=(selected_model is None),
)

with st.sidebar.expander("📖 Jargon Buster"):
    st.markdown("""
    - **Confidence**: AI's certainty (0-100%).
    - **Stop Loss**: Safety level to minimize downside.
    - **Target**: Predicted price goals.
    - **Drivers**: Factors most influencing this signal.
    """)

# ── Main Panel: Prediction ────────────────────────────────────
if predict_btn:
        model_name_full = f"{selected_model['model_name']}_v{selected_model['version']}"
        days_param = predict_days if selected_framework == "prophet" else 5
        
        with st.spinner(f"AI is analyzing {ticker} trends..."):
            try:
                result = DashboardService.fetch_predictions("", "", days_param, model_name_full)
            except Exception as e:
                result = {"error": str(e)}

        if not isinstance(result, dict) or result.get("error"):
            st.error(f"⚠️ Prediction failed: {result.get('error', 'Unknown')}")
        else:
            # Standardized Prediction Card
            pred = result.get("predictions", {})
            st.subheader("🎯 AI Prediction Signal")
            
            direction = pred.get("direction", "HOLD")
            confidence = pred.get("confidence", 0.0)
            signals = {"BUY": "🟢", "HOLD": "🟡", "AVOID": "🔴"}
            
            with st.container(border=True):
                col_header, col_conf = st.columns([2, 1])
                with col_header:
                    st.write(f"### {signals.get(direction, '🟡')} {direction}")
                    st.write(f"**Horizon:** {pred.get('horizon', 'N/A')}")
                with col_conf:
                    st.metric("Confidence", f"{confidence:.0%}")
                
                st.divider()
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Target Low", format_currency(pred.get('target_low', 0)))
                m2.metric("Target High", format_currency(pred.get('target_high', 0)))
                m3.metric("Stop Loss", format_currency(pred.get('stop_loss', 0)))
                m4.metric("Risk Level", pred.get("risk_level", "MEDIUM"))

                # Conditional Sections
                if pred.get("key_drivers") or pred.get("bear_case"):
                    st.divider()
                    
                    drv_col, bear_col = st.columns(2)
                    with drv_col:
                        if pred.get("key_drivers"):
                            st.write("**🧠 Key Drivers:**")
                            for driver in pred["key_drivers"]:
                                st.write(f"- {driver}")
                    with bear_col:
                        if pred.get("bear_case"):
                            st.warning(f"🐻 **Bear Case:** {pred['bear_case']}")

                # Model Specific Views (e.g. Prophet Charts)
                if selected_framework == "prophet" and pred.get("forecast_data"):
                    st.divider()
                    st.write("**📈 Forecast Visualization**")
                    forecast_df = pd.DataFrame(pred["forecast_data"])
                    forecast_df['date'] = pd.to_datetime(forecast_df['date'])
                    
                    fig = go.Figure()
                    # Predicted Value
                    fig.add_trace(go.Scatter(
                        x=forecast_df['date'], y=forecast_df['value'],
                        name='Predicted', line=dict(color='#00FFA3', width=3)
                    ))
                    # Uncertainty Interval
                    fig.add_trace(go.Scatter(
                        x=pd.concat([forecast_df['date'], forecast_df['date'][::-1]]),
                        y=pd.concat([forecast_df['upper_bound'], forecast_df['lower_bound'][::-1]]),
                        fill='toself', fillcolor='rgba(0, 255, 163, 0.1)',
                        line=dict(color='rgba(255,255,255,0)'),
                        hoverinfo="skip", showlegend=False
                    ))
                    
                    fig.update_layout(
                        template="plotly_dark",
                        height=400,
                        margin=dict(l=20, r=20, t=20, b=20),
                        xaxis=dict(showgrid=False),
                        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
                    )
                    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("ℹ️ Select a stock models from the sidebar and click **Run Prediction** to generate AI signals.")
