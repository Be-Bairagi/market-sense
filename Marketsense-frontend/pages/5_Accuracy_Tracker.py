import logging
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from services.dashboard_service import DashboardService
from data.nifty50 import NIFTY_50_SYMBOLS, NIFTY_50_MAP
from utils.helpers import CURRENCY_SYMBOL, initialize_ui_context
from components.accuracy_components import (
    render_health_chips,
    render_hero_accuracy,
    render_kpi_cards,
    render_confusion_matrix,
    render_residuals,
    render_academic_summary,
    render_training_metadata
)
from components.loader import render_loader

logger = logging.getLogger(__name__)

# Initialize Global UI
initialize_ui_context()

if 'available_models' not in st.session_state:
    st.session_state.available_models = []
if 'models_ticker' not in st.session_state:
    st.session_state.models_ticker = None

# ── Page Setup ────────────────────────────────────────────────
st.set_page_config(
    page_title="Model Insights | MarketSense", page_icon="🧠", layout="wide"
)

st.title("🧠 Model Insights & Performance Dashboard")
st.markdown(
    "Transparent, data-driven view of how your AI models perform over time. "
    "Switch to **Beginner** mode in Home for simpler explanations."
)
st.markdown("---")

# Sidebar Configuration
st.sidebar.header("🔎 Stock Selection")
from utils.helpers import get_default_ticker_index
ticker_options = [f"{NIFTY_50_MAP[s]} ({s})" for s in NIFTY_50_SYMBOLS]
default_idx = get_default_ticker_index(NIFTY_50_SYMBOLS)
selected_option = st.sidebar.selectbox("Select Stock:", ticker_options, index=default_idx)
ticker = selected_option.split(" (")[-1].rstrip(")")

st.sidebar.divider()
st.sidebar.header("📊 Model Selection")

# 1. Fetch available models for the selected ticker (with caching)
if st.session_state.models_ticker != ticker:
    with render_loader("Loading models"):
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
    model_type = None
else:
    def _model_label(m: dict) -> str:
        fw = m["framework"].upper()
        badge = "Active" if m["is_active"] else "Inactive"
        return f"{m['model_name']}_v{m['version']} ({fw} · {badge})"

    model_labels = [_model_label(m) for m in available_models]
    
    # Default to saved framework, else hybrid, else 0
    default_fw = st.session_state.get("default_model_framework")
    default_model_idx = 0
    if default_fw:
        for i, m in enumerate(available_models):
            if m["framework"] == default_fw:
                default_model_idx = i
                break
    else:
        # Fallback to hybrid
        default_model_idx = next((i for i, m in enumerate(available_models) if "hybrid" in m["framework"].lower()), 0)
    
    chosen_label = st.sidebar.selectbox(
        "Select Model:",
        model_labels,
        index=default_model_idx,
    )
    chosen_idx = model_labels.index(chosen_label)
    selected_model = available_models[chosen_idx]
    model_type = selected_model["framework"]

    # Model Details
    active_tag = "✅ Active" if selected_model["is_active"] else "⏸ Inactive"
    st.sidebar.write(f"**Framework:** {model_type.upper()}")
    st.sidebar.write(f"**Version:** v{selected_model['version']}")
    st.sidebar.write(f"**Status:** {active_tag}")

period = st.sidebar.selectbox(
    "Evaluation Period", ["7d", "30d", "90d", "180d", "1y"], index=2
)
st.sidebar.markdown("---")


# ── Performance Chart Helper ──────────────────────────────────
def render_page_performance_chart(df, metrics, model_category):
    st.subheader("📊 Performance Visualization")
    
    if metrics.get("eval_status") == "stored_metrics_only":
        st.info("📊 **Live chart not available for LSTM** — This model uses stored training metrics. "
                "A live evaluation chart will be available in a future update. All accuracy metrics "
                "shown above are from the model's out-of-sample test set during training.")
        return

    if df.empty or "actual" not in df.columns:
        st.warning("No prediction data available for visualization.")
        return

    fig = go.Figure()
    # Actual Price Line
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["actual"],
        mode="lines", name="Actual Price",
        line=dict(color="#2563eb", width=2),
    ))

    if model_category == "regression" and "predicted" in df.columns:
        # Forecasted Price
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["predicted"],
            mode="lines", name="Predicted Price",
            line=dict(color="#f59e0b", width=2, dash='dot'),
        ))
        
        # Confidence Band
        if "lower_bound" in df.columns and "upper_bound" in df.columns:
            fig.add_trace(go.Scatter(
                x=df["date"].tolist() + df["date"].tolist()[::-1],
                y=df["upper_bound"].tolist() + df["lower_bound"].tolist()[::-1],
                fill="toself",
                fillcolor="rgba(37, 99, 235, 0.1)",
                line=dict(color="rgba(37, 99, 235, 0)"),
                name="Confidence Interval",
                hoverinfo='skip'
            ))
            
    elif model_category == "classification" and "signal" in df.columns:
        # AI Signals (Markers)
        buys = df[df["signal"] == "BUY"]
        avoids = df[df["signal"] == "AVOID"]
        
        fig.add_trace(go.Scatter(
            x=buys["date"], y=buys["actual"],
            mode="markers", name="AI: BUY",
            marker=dict(color="#22c55e", size=10, symbol="triangle-up"),
        ))
        fig.add_trace(go.Scatter(
            x=avoids["date"], y=avoids["actual"],
            mode="markers", name="AI: AVOID",
            marker=dict(color="#ef4444", size=10, symbol="triangle-down"),
        ))
        
        # Wrong Calls (Actual != Predicted)
        if "label" in df.columns:
            wrong = df[df["signal"] != df["label"]]
            if not wrong.empty:
                fig.add_trace(go.Scatter(
                    x=wrong["date"], y=wrong["actual"],
                    mode="markers", name="❌ Wrong Prediction",
                    marker=dict(color="#ef4444", size=8, symbol="x"),
                    hoverinfo='text',
                    text=[f"Predicted {s}, but actually {l}" for s, l in zip(wrong["signal"], wrong["label"])]
                ))

    fig.update_layout(
        yaxis_title=f"Price ({CURRENCY_SYMBOL})",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        margin=dict(t=80, b=20, l=0, r=0)
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Main Content ──────────────────────────────────────────────
if model_type:
    try:
        is_beginner = st.session_state.get("user_mode", "💡 Beginner") == "💡 Beginner"

        # 1. API Fetch
        with render_loader(f"AI Engine is evaluating {ticker}"):
            eval_url = (
                f"http://127.0.0.1:8000/api/v1/evaluate"
                f"?ticker={ticker}&period={period}&model_type={model_type}"
            )
            eval_response = requests.get(eval_url)

        if eval_response.status_code != 200:
            detail = eval_response.json().get("detail", "N/A")
            st.warning(f"🔔 **Insight Notice**: {detail}")
            st.info("Try selecting a different evaluation period or ensure the model is fully trained.")
        else:
            metrics = eval_response.json()
            model_category = metrics.get("model_category", "regression")
            df = pd.DataFrame(metrics.get("predictions", []))
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"])

            # ── Section 1: Health Chips ──
            render_health_chips(metrics)
            st.write("")

            # ── Section 2: Hero Accuracy ──
            render_hero_accuracy(metrics, is_beginner)
            
            # ── Section 3: KPI Metrics ──
            st.subheader(f"📈 Performance Overview — {ticker}")
            render_kpi_cards(metrics, model_category, is_beginner)
            st.markdown("---")

            # ── Section 4: Performance Chart ──
            render_page_performance_chart(df, metrics, model_category)
            st.markdown("---")

            # ── Section 5: Deep Dive ──
            col_dd1, col_dd2 = st.columns([1.2, 1])
            with col_dd1:
                if model_category == "classification":
                    render_confusion_matrix(metrics, is_beginner)
                else:
                    render_residuals(df, model_category, is_beginner)
            
            with col_dd2:
                # ── Section 6: Feature Importance ──
                st.subheader("🔍 Feature Importance")
                feat_data = metrics.get("feature_importance")
                
                if feat_data and feat_data.get("Weight") and any(w > 0 for w in feat_data["Weight"]):
                    df_feat = pd.DataFrame(feat_data)
                    # Sort by weight
                    df_feat = df_feat.sort_values(by="Weight", ascending=False).head(10)
                    
                    fig_feat = px.bar(
                        df_feat, x="Weight", y="Feature",
                        orientation="h", color="Weight",
                        color_continuous_scale="Blues",
                    )
                    fig_feat.update_layout(
                        height=400, template="plotly_white",
                        yaxis=dict(autorange="reversed"),
                        margin=dict(t=20, b=20, l=0, r=0)
                    )
                    st.plotly_chart(fig_feat, use_container_width=True)
                else:
                    st.info(f"Feature importance detail is not yet available for this {model_type} model.")

            # ── Section 7: Academic & Meta ──
            st.markdown("---")
            render_academic_summary(metrics, period)
            render_training_metadata(metrics)

    except Exception as e:
        logger.exception("Error fetching insights")
        st.error("⚠️ We encountered an issue while loading insights. Please try selecting a different period or model.")
else:
    # ── Landing State ────
    st.info("ℹ️ No trained models found for this stock. Please select a stock with trained models or go to **Model Management** to train a new one.")
    

