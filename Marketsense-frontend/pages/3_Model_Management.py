from datetime import datetime
import time

import requests
import streamlit as st
import utils.helpers as helpers
from services.model_service import ModelService

if "models_cache" not in st.session_state:
    st.session_state.models_cache = None

if "models_loaded" not in st.session_state:
    st.session_state.models_loaded = False

st.set_page_config(page_title="Model Management | MarketSense", layout="wide")

st.title("⚙️ Model Management")
st.write("Manage model training, retraining, and configurations here.")

st.markdown("---")

# --- Initialize session state ---
if "active_model" not in st.session_state:
    st.session_state.active_model = ""

model = st.session_state.active_model

# --- Section 0: Select Model ---
st.subheader("📈 Select Model")

with st.form("select_model_form"):
    model_type = st.selectbox("Select Model", ["Prophet"], index=0)
    submitted = st.form_submit_button("Activate Model")

if submitted:
    # Convert to lowercase for backend API
    model_key = helpers.to_snake_case(model_type)
    st.session_state.active_model = model_key
    model = st.session_state.active_model
    st.success(f"✅ Model '{model_type}' activated for training and predictions.")

# --- Section 1: Train New Model ---
st.subheader("🚀 Train New Model")

if model:
    st.info(f"Currently active model: **{model}**")
else:
    st.warning("No model currently active.")

with st.form("train_model_form"):
    ticker = st.text_input("Enter Stock Ticker Symbol (e.g. AAPL, TSLA, INFY.NS)", "")
    period = st.selectbox(
        "Select Data Period for Training",
        ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
        index=2,
    )
    submitted = st.form_submit_button("Start Training")

if submitted:
    if not ticker:
        st.warning("Please enter a ticker symbol before training.")
    elif not model:
        st.warning("Please activate a model before training.")
    else:
        try:
            # Progress tracking UI
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.info(f"🚀 Starting training for {ticker}...")
            progress_bar.progress(10)
            
            status_text.info("📊 Fetching historical data...")
            progress_bar.progress(30)
            
            status_text.info(f"🧠 Training {model} model...")
            progress_bar.progress(60)
            
            with st.spinner(f"Training model '{model}' for {ticker}..."):
                result = ModelService.train_model(ticker, period, model)
            
            progress_bar.progress(90)
            status_text.info("💾 Saving model artifact...")
            
            with st.spinner(f"Training model '{model}' for {ticker}..."):
                result = ModelService.train_model(ticker, period, model)
            
            if not result.get("error"):
                progress_bar.progress(100)
                status_text.success("✅ Training complete!")
                
                # Short delay then clear progress UI
                time.sleep(1)
                progress_bar.empty()
                status_text.empty()
                
                st.success("✅ Model trained successfully!")

                # --- Training summary section ---
                st.markdown("### 📊 Training Summary")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Model Type", result.get("model_name", model))
                with col2:
                    st.metric("Ticker", ticker)
                with col3:
                    st.metric("Period", period)

                st.write("**Training Date:**", datetime.now().strftime("%d-%m-%Y"))
                st.write("**Saved Path:**", result.get("artifact_path", "N/A"))

                # --- Metrics section ---
                metrics = result.get("training_metrics", {})
                if metrics:
                    st.markdown("### 📈 Performance Metrics")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("MAE", f"{metrics.get('MAE', 'N/A')}")
                    m2.metric("RMSE", f"{metrics.get('RMSE', 'N/A')}")
                    m3.metric("R²", f"{metrics.get('R2', 'N/A')}")

                # --- Actions ---
                st.markdown("### 🧩 Next Actions")
                st.write("✅ You can now:")
                st.markdown("""
                - 📉 Use this model for predictions
                - 🔁 Retrain with updated data
                - 💾 Download model artifact (coming soon)
                """)

            else:
                st.error(f"❌ Training failed: {result.get('error')}")

        except requests.exceptions.RequestException as e:
            st.error(f"Failed to connect to backend: {e}")

st.markdown("---")

# --- Section 2: Model Registry (Placeholder) ---
st.subheader("🗂️ Model Registry")

if not st.session_state.models_loaded:
    with st.spinner("🔄 Loading trained models from registry..."):
        st.session_state.models_cache = ModelService.get_all_models()
        st.session_state.models_loaded = True

if submitted:
    with st.spinner("🔄 Refreshing model registry..."):
        st.session_state.models_cache = ModelService.get_all_models()

if (
    st.session_state.models_cache is not None
    and not isinstance(st.session_state.models_cache, dict)
    and not st.session_state.models_cache.empty
):
    res = st.session_state.models_cache
    # render dataframe here
    st.dataframe(
        res,
        width="stretch",
        hide_index=True,
    )
else:
    st.warning("No trained models found.")
