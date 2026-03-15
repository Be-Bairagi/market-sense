import datetime
import logging
import re

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from services.model_service import ModelService

logger = logging.getLogger(__name__)

# ── Page Setup ────────────────────────────────────────────────
st.set_page_config(
    page_title="Model Insights | MarketSense", page_icon="🧠", layout="wide"
)
st.title("🧠 Model Insights & Performance Dashboard")
st.markdown(
    "Transparent, data-driven view of how your AI models perform over time."
)
st.markdown("---")

# ── Sidebar ───────────────────────────────────────────────────
st.sidebar.header("📊 Model Evaluation Settings")

# Fetch available models dynamically
try:
    models_resp = ModelService.get_model_list()
    if models_resp.get("models"):
        model_list = [
            f"{m['ticker']} ({m['model_type']}, trained {m['date_trained']})"
            for m in models_resp["models"]
        ]
    else:
        model_list = ["No models available"]
except Exception:
    logger.exception("Failed to fetch available models")
    model_list = ["No models available"]

selected_model = st.sidebar.selectbox("Select a trained model", model_list)
period = st.sidebar.selectbox(
    "Evaluation Period", ["7d", "30d", "90d", "180d"], index=1
)
st.sidebar.markdown("---")
refresh = st.sidebar.button("🔄 Refresh Insights")

# ── Main Content ──────────────────────────────────────────────
if refresh and "No models" not in selected_model:
    try:
        # Parse ticker and model type
        match = re.match(r"(\S+)\s+\(([^,]+)", selected_model)
        if not match:
            st.error("Could not parse selected model.")
            raise ValueError("Invalid model string format.")

        ticker = match.group(1).strip()
        model_type = match.group(2).strip()

        is_xgboost = model_type.lower() == "xgboost"

        eval_url = (
            f"http://127.0.0.1:8000/api/v1/evaluate"
            f"?ticker={ticker}&period={period}&model_type={model_type}"
        )
        eval_response = requests.get(eval_url)

        if eval_response.status_code != 200:
            detail = eval_response.json().get("detail", "N/A")
            st.error(f"Failed to fetch metrics. Status: {eval_response.status_code}. {detail}")
        else:
            metrics = eval_response.json()

            # ── KPI Section ────
            st.subheader(f"📈 Performance Overview — {ticker}")

            if is_xgboost:
                kpi1, kpi2, kpi3 = st.columns(3)
                kpi1.metric(
                    "Directional Accuracy",
                    f"{metrics.get('accuracy', metrics.get('R2', 0)):.1%}"
                    if isinstance(metrics.get('accuracy', metrics.get('R2', 0)), float)
                    else str(metrics.get('accuracy', 'N/A'))
                )
                kpi2.metric("Data Points", metrics.get("data_points", "N/A"))
                kpi3.metric("Model Type", "XGBoost Classifier")
            else:
                kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                kpi1.metric("MAE", f"{metrics.get('MAE', 0):.3f}")
                kpi2.metric("RMSE", f"{metrics.get('RMSE', 0):.3f}")
                kpi3.metric("R² Score", f"{metrics.get('R2', 0):.3f}")
                kpi4.metric("Data Points", metrics.get("data_points", "N/A"))

            st.markdown("---")

            # ── Prediction vs Actual Chart ────
            if "predictions" in metrics:
                df = pd.DataFrame(metrics["predictions"])
                if not df.empty and all(k in df.columns for k in ["date", "actual", "predicted"]):
                    df["date"] = pd.to_datetime(df["date"])
                    st.subheader("📊 Actual vs Predicted")

                    fig = go.Figure()

                    if "lower_bound" in df.columns and "upper_bound" in df.columns:
                        fig.add_trace(go.Scatter(
                            x=df["date"].tolist() + df["date"].tolist()[::-1],
                            y=df["upper_bound"].tolist() + df["lower_bound"].tolist()[::-1],
                            fill="toself",
                            fillcolor="rgba(37, 99, 235, 0.12)",
                            line=dict(color="rgba(37, 99, 235, 0)"),
                            name="Confidence Interval",
                        ))

                    fig.add_trace(go.Scatter(
                        x=df["date"], y=df["actual"],
                        mode="lines", name="Actual",
                        line=dict(color="#1f77b4", width=2),
                    ))
                    fig.add_trace(go.Scatter(
                        x=df["date"], y=df["predicted"],
                        mode="lines", name="Predicted",
                        line=dict(color="#ff7f0e", width=2),
                    ))
                    fig.update_layout(
                        yaxis_title="Price (₹)", template="plotly_white",
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Residuals
                    df["residual"] = df["actual"] - df["predicted"]
                    st.subheader("📉 Residual Distribution")
                    fig_resid = px.histogram(df, x="residual", nbins=25)
                    fig_resid.update_layout(template="plotly_white")
                    st.plotly_chart(fig_resid, use_container_width=True)

            # ── Feature Importance ────
            st.subheader("🔍 Feature Importance")
            feat_data = metrics.get("feature_importance", None)
            model_summary_name = metrics.get("model_type", "Unknown")

            if feat_data and feat_data.get("Weight", ["N/A"])[0] != "N/A":
                df_feat = pd.DataFrame(feat_data)
                fig_feat = px.bar(
                    df_feat, x="Weight", y="Feature",
                    orientation="h", color="Weight",
                    color_continuous_scale="Blues",
                )
                fig_feat.update_layout(
                    height=400, template="plotly_white",
                    yaxis=dict(autorange="reversed"),
                )
                st.plotly_chart(fig_feat, use_container_width=True)
            else:
                if is_xgboost:
                    st.info("Feature importance will be available after model evaluation is implemented for XGBoost.")
                else:
                    st.info(f"Feature importance is not available for {model_summary_name} models.")

            # ── Model Summary ────
            st.markdown("### 🧾 Model Summary")
            st.write(f"""
            **Model:** {model_summary_name}
            **Ticker:** {ticker}
            **Evaluation Period:** {period}
            **Trained On:** {metrics.get('trained_on', datetime.date.today())}
            """)

    except Exception as e:
        logger.exception("Error fetching insights")
        st.error(f"⚠️ Error: {e}")
else:
    st.info("ℹ️ Select a trained model from the sidebar and click **Refresh Insights**.")
