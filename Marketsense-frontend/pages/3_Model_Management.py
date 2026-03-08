import time
from datetime import datetime

import plotly.express as px
import requests
import streamlit as st
import utils.helpers as helpers
from data.nifty50 import NIFTY_50_SYMBOLS, NIFTY_50_MAP
from services.dashboard_service import DashboardService
from services.model_service import ModelService

if "models_cache" not in st.session_state:
    st.session_state.models_cache = None
if "models_loaded" not in st.session_state:
    st.session_state.models_loaded = False

st.set_page_config(page_title="Model Management | MarketSense", layout="wide")

st.title("⚙️ Model Management")
st.write("Train, manage, and monitor ML models for stock prediction.")

st.markdown("---")

# ── Section 0: Select Model ──────────────────────────────────
st.subheader("📈 Select Model")

model_type = st.selectbox("Model Framework", ["XGBoost", "Prophet"], index=0)
model_key = helpers.to_snake_case(model_type)

st.markdown("---")

# ── Section 1: Train New Model ───────────────────────────────
st.subheader("🚀 Train New Model")
st.info(f"Active framework: **{model_type}**")

# Ticker selection
ticker_options = [f"{s} — {NIFTY_50_MAP[s]}" for s in NIFTY_50_SYMBOLS]
selected = st.selectbox("Stock Ticker", ticker_options, index=0)
ticker = selected.split(" — ")[0]

if model_type == "XGBoost":
    # ── XGBoost Prerequisites ────
    st.markdown("### 📋 Training Prerequisites")
    st.caption("XGBoost requires historical data + computed feature vectors before training.")

    col_chk1, col_chk2 = st.columns(2)

    with col_chk1:
        if st.button("🔍 Check Data Status", use_container_width=True):
            data_status = DashboardService.fetch_data_status()
            feature_status = DashboardService.fetch_feature_status()

            if data_status.get("error"):
                st.error(f"❌ Could not check data status: {data_status['error']}")
            else:
                stocks = data_status.get("unique_stocks_cached", 0)
                st.metric("Stocks with Price Data", stocks)

            if feature_status.get("error"):
                st.error(f"❌ Could not check feature status: {feature_status['error']}")
            else:
                fv_count = feature_status.get("total_feature_vectors", 0)
                fv_symbols = feature_status.get("unique_symbols", 0)
                st.metric("Feature Vectors", fv_count)
                st.metric("Symbols with Features", fv_symbols)

    with col_chk2:
        st.markdown("**Quick Setup Pipeline:**")
        if st.button("1️⃣ Backfill Price Data", use_container_width=True):
            with st.spinner(f"Starting price backfill for {ticker}..."):
                res = DashboardService.backfill_data(ticker)
            if res.get("error"):
                st.error(f"❌ {res['error']}")
            else:
                st.success(f"✅ {res.get('message', 'Backfill started!')}")
                st.info("⏳ This runs in the background. Wait ~1 min for 5 years of data.")

        if st.button("2️⃣ Compute Features", use_container_width=True):
            with st.spinner(f"Starting feature backfill for {ticker}..."):
                res = DashboardService.backfill_features(ticker)
            if res.get("error"):
                st.error(f"❌ {res['error']}")
            else:
                st.success(f"✅ {res.get('message', 'Feature computation started!')}")
                st.info("⏳ This runs in the background. Wait ~5 min for full backfill.")

    st.markdown("---")

# ── Training form ────
with st.form("train_model_form"):
    if model_type == "Prophet":
        period = st.selectbox(
            "Training Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=2
        )
    else:
        period = "5y"
        st.info("XGBoost trains on all available feature vectors (default 5-year range).")

    submitted = st.form_submit_button(
        f"🧠 Train {model_type} Model", use_container_width=True
    )

if submitted:
    try:
        progress_bar = st.progress(0)
        status_text = st.empty()

        status_text.info(f"🚀 Starting {model_type} training for {ticker}...")
        progress_bar.progress(10)

        status_text.info("📊 Fetching data & computing features...")
        progress_bar.progress(30)

        status_text.info(f"🧠 Training {model_type} model...")
        progress_bar.progress(60)

        with st.spinner(f"Training {model_type} for {ticker}..."):
            result = ModelService.train_model(ticker, period, model_key)

        progress_bar.progress(90)
        status_text.info("💾 Saving model artifact...")

        if not result.get("error"):
            progress_bar.progress(100)
            status_text.success("✅ Training complete!")
            time.sleep(1)
            progress_bar.empty()
            status_text.empty()

            st.success("✅ Model trained successfully!")

            # ── Training Summary ────
            st.markdown("### 📊 Training Summary")
            c1, c2, c3 = st.columns(3)
            c1.metric("Model", result.get("model_name", model_key))
            c2.metric("Ticker", ticker)
            c3.metric("Version", result.get("version", "N/A"))

            st.write(f"**Trained:** {datetime.now().strftime('%d-%m-%Y %H:%M')}")
            st.write(f"**Artifact:** {result.get('artifact_path', 'N/A')}")

            # ── Metrics ────
            metrics = result.get("training_metrics", {})
            if metrics:
                st.markdown("### 📈 Performance Metrics")
                if model_type == "XGBoost":
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Accuracy", f"{metrics.get('accuracy', 'N/A')}")
                    m2.metric("Train Size", f"{metrics.get('train_size', 'N/A')}")
                    m3.metric("Test Size", f"{metrics.get('test_size', 'N/A')}")

                    # Feature importance chart
                    top_features = metrics.get("top_features", {})
                    if top_features:
                        st.markdown("### 🔍 Top Feature Importances")
                        import pandas as pd
                        df_feat = pd.DataFrame(
                            sorted(top_features.items(), key=lambda x: x[1], reverse=True)[:15],
                            columns=["Feature", "Importance"]
                        )
                        fig = px.bar(
                            df_feat, x="Importance", y="Feature",
                            orientation="h", color="Importance",
                            color_continuous_scale="Blues",
                        )
                        fig.update_layout(
                            height=400, template="plotly_white",
                            yaxis=dict(autorange="reversed"),
                        )
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    m1, m2, m3 = st.columns(3)
                    m1.metric("MAE", f"{metrics.get('MAE', 'N/A')}")
                    m2.metric("RMSE", f"{metrics.get('RMSE', 'N/A')}")
                    m3.metric("R²", f"{metrics.get('R2', 'N/A')}")
        else:
            st.error(f"❌ Training failed: {result.get('error')}")

    except requests.exceptions.RequestException as e:
        st.error(f"Failed to connect to backend: {e}")

st.markdown("---")

# ── Section 2: Model Registry ────────────────────────────────
st.subheader("🗂️ Model Registry")

if not st.session_state.models_loaded:
    with st.spinner("🔄 Loading models from registry..."):
        st.session_state.models_cache = ModelService.get_all_models()
        st.session_state.models_loaded = True

if submitted:
    with st.spinner("🔄 Refreshing registry..."):
        st.session_state.models_cache = ModelService.get_all_models()

if (
    st.session_state.models_cache is not None
    and not isinstance(st.session_state.models_cache, dict)
    and not st.session_state.models_cache.empty
):
    st.dataframe(
        st.session_state.models_cache,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.warning("No trained models found in registry.")
