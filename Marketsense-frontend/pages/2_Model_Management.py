import time
import requests
import pandas as pd
import plotly.express as px
import streamlit as st
import utils.helpers as helpers
from utils.helpers import format_currency, initialize_ui_context
from datetime import datetime
from data.nifty50 import NIFTY_50_SYMBOLS, NIFTY_50_MAP
from services.dashboard_service import DashboardService
from services.model_service import ModelService
from components.loader import render_loader

# ── Session State ─────────────────────────────────────────────
# Initialize Global UI
initialize_ui_context()

if "models_cache" not in st.session_state:
    st.session_state.models_cache = None
if "models_loaded" not in st.session_state:
    st.session_state.models_loaded = False

st.set_page_config(
    page_title="Model Management | MarketSense",
    page_icon="⚙️",
    layout="wide"
)

# Sidebar logic handled by initialize_ui_context

st.title("⚙️ Model Management")
st.write("Configure and train AI models for stock price prediction.")

st.divider()

# ── Compact Configuration Row ────────────────────────────────
st.subheader("🚀 Train New Model")

# Prepare ticker options
ticker_options = [f"{s} — {NIFTY_50_MAP[s]}" for s in NIFTY_50_SYMBOLS]

# Single row for all inputs to avoid scrolling
conf_col1, conf_col2, conf_col3 = st.columns(3)

with conf_col1:
    model_type = st.selectbox("AI Framework", ["XGBoost", "Prophet", "LSTM", "Hybrid Ensemble"], index=0)
    # Backend expects 'xgboost', 'prophet' or 'lstm'
    model_map = {"XGBoost": "xgboost", "Prophet": "prophet", "LSTM": "lstm", "Hybrid Ensemble": "hybrid"}
    model_key = model_map.get(model_type, "xgboost")

    if model_type == "Hybrid Ensemble":
        st.info("🧠 **Hybrid Ensemble** combines all models for highest accuracy (Targets 85-92%). Training takes ~3-5 mins.")

with conf_col2:
    from utils.helpers import get_default_ticker_index
    default_idx = get_default_ticker_index(NIFTY_50_SYMBOLS)
    selected_ticker = st.selectbox("Target Stock", ticker_options, index=default_idx)
    ticker = selected_ticker.split(" — ")[0]

with conf_col3:
    if model_type == "Prophet":
        period = st.selectbox(
            "Training Period", 
            ["1mo", "3mo", "6mo", "1y", "2y", "5y"], 
            index=3,
            help="Prophet works best with more history (1y+)."
        )
    else:
        # XGBoost and LSTM both require long-term history for feature store / sequence context
        period = "5y"
        st.selectbox("Training Period", ["5y (Full History)"], index=0, disabled=True)

# Training Action
st.write("")
train_col1, train_col2 = st.columns([1, 4])
with train_col1:
    train_submitted = st.button("🔥 Start Training", type="primary", use_container_width=True)

# ── Unified Training Logic ───────────────────────────────────
if train_submitted:
    try:
        with st.status(f"Training {model_type} for {ticker}...", expanded=True) as status:
            # 1. Automatic Prerequisite Check & Initialization
            status.write("🔍 Initializing training data & features...")
            
            # --- Sub-step: Data Coverage ---
            data_status = DashboardService.fetch_ticker_data_status(ticker)
            if not data_status.get("sufficient_for_features", False):
                status.write(f"📥 Insufficient price data ({data_status.get('count', 0)}/300 days). Triggering backfill...")
                DashboardService.backfill_data(ticker)
                
                # Poll for up to 60 seconds
                for i in range(12):
                    time.sleep(5)
                    data_status = DashboardService.fetch_ticker_data_status(ticker)
                    status.write(f"⏳ Synchronizing price data... {data_status.get('count', 0)}/300 days")
                    if data_status.get("sufficient_for_features"):
                        status.write("✅ Price data synchronized.")
                        break
                else:
                    status.update(label="❌ Data synchronization timed out", state="error")
                    st.error(f"Could not fetch enough historical data for {ticker}. Please try again later.")
                    st.stop()
            else:
                status.write("✅ Historical price data sufficient.")

            # --- Sub-step: Feature Store ---
            if model_type in ["XGBoost", "LSTM"]:
                feat_status = DashboardService.fetch_ticker_feature_status(ticker)
                if not feat_status.get("sufficient_for_training", False):
                    status.write(f"🏗️ Insufficient features ({feat_status.get('count', 0)}/100 vectors). Computing...")
                    DashboardService.backfill_features(ticker)
                    
                    # Poll for up to 60 seconds
                    for i in range(12):
                        time.sleep(5)
                        feat_status = DashboardService.fetch_ticker_feature_status(ticker)
                        status.write(f"⏳ Computing feature vectors... {feat_status.get('count', 0)}/100")
                        if feat_status.get("sufficient_for_training"):
                            status.write("✅ Feature store ready.")
                            break
                    else:
                        status.update(label="❌ Feature computation timed out", state="error")
                        st.error(f"{model_type} training requires 100+ daily feature vectors. Only {feat_status.get('count', 0)} computed so far.")
                        st.stop()
                else:
                    status.write("✅ Feature store ready.")
            
            # Final short pause for stability
            time.sleep(1)
            
            # 2. Actual Training Call
            status.write("🧠 Executing model training...")
            result = ModelService.train_model(ticker, period, model_key)
            
            if result.get("error"):
                if result["error"] == "no_improvement":
                    status.update(label="⚠️ Retraining aborted (no improvement)", state="complete")
                    st.warning(
                        f"Retraining for **{ticker}** aborted. The new model version did not outperform the "
                        "currently active one. Your active model remains unchanged."
                    )
                    # Show metrics if available
                    c1, c2 = st.columns(2)
                    with c1: st.metric("Active Model Score", result.get("old_metrics", {}).get("accuracy" if model_type == "XGBoost" else "R2", "N/A"))
                    with c2: st.metric("New Model Score", result.get("new_metrics", {}).get("accuracy" if model_type == "XGBoost" else "R2", "N/A"), delta="Rejected", delta_color="inverse")
                else:
                    status.update(label=f"❌ Training Failed: {result['error']}", state="error")
                    st.error(f"Failed to train {model_type} for {ticker}: {result['error']}")
            else:
                status.update(label=f"✅ {model_type} Trained Successfully!", state="complete")
                
                # Set persistent notice for after rerun
                ver = result.get('version', '?')
                m_name = result.get('model_name', ticker)
                st.session_state.training_success_notice = (
                    f"Model **{m_name}** (v{ver}) has been trained and activated successfully! "
                    "You can now use it for predictions on the Dashboard."
                )

                # Success Summary (visible for a moment before rerun)
                with st.container(border=True):
                    st.write(f"### 🎉 {ticker} Prediction Engine Ready")
                    st.write(f"**Model:** {result.get('model_name')} | **Version:** v{result.get('version')}")
                    
                    ms1, ms2, ms3 = st.columns(3)
                    metrics = result.get("training_metrics", {})
                    if model_type in ["XGBoost", "LSTM"]:
                        ms1.metric("Accuracy", f"{metrics.get('accuracy', 0):.1%}")
                        ms2.metric("Train Size", metrics.get("train_size", "N/A"))
                        ms3.metric("Test Size", metrics.get("test_size", "N/A"))
                    else:
                        ms1.metric("MAE", format_currency(metrics.get('MAE', 0)))
                        ms2.metric("R² Score", f"{metrics.get('R2', 0):.3f}")
                        ms3.metric("RMSE", format_currency(metrics.get('RMSE', 0)))

                # Refresh registry
                st.session_state.pop("available_models", None)
                st.session_state.pop("models_ticker", None)
                st.session_state.models_loaded = False
                st.rerun()

    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

st.divider()

# ── Notifications ─────────────────────────────────────────────
if "training_success_notice" in st.session_state:
    st.success(st.session_state.training_success_notice, icon="✅")
    if st.button("Clear Notification"):
        del st.session_state.training_success_notice
        st.rerun()

# ── Section 2: Model Registry ────────────────────────────────
st.subheader("🗂️ Model Registry")

if not st.session_state.models_loaded:
    with render_loader("Syncing registry"):
        st.session_state.models_cache = ModelService.get_all_models()
        st.session_state.models_loaded = True

mc = st.session_state.models_cache

if isinstance(mc, dict) and "error" in mc:
    st.error(f"❌ Connection Error: {mc['error']}")
    if st.button("🔄 Retry Sync"):
        st.session_state.models_loaded = False
        st.rerun()
elif mc is not None and not mc.empty:
    # Filter to only show active models as requested
    active_models = mc[mc["Status"] == "✅ Active"]
    st.write(f"Showing {len(active_models)} active models in the registry.")
    
    st.dataframe(
        active_models,
        use_container_width=True,
        hide_index=True,
    )
    
    if st.button("🔄 Refresh List", use_container_width=True):
        st.session_state.models_loaded = False
        st.rerun()
else:
    st.info("ℹ️ Your model registry is currently empty. Train a model above to see it here.")
