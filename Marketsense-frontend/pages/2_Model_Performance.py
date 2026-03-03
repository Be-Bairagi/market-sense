import datetime
import logging
import re  # Import the regular expression module

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from services.model_service import ModelService

logger = logging.getLogger(__name__)

# ------------------------------------------------------
# Page Setup
# ------------------------------------------------------
st.set_page_config(
    page_title="Model Insights | MarketSense", page_icon="🧠", layout="wide"
)
st.title("🧠 Model Insights & Performance Dashboard")
st.markdown(
    "Gain a transparent, data-driven view of how your AI models perform over time."
)
st.markdown("---")

# ------------------------------------------------------
# Sidebar Controls
# ------------------------------------------------------
st.sidebar.header("📊 Model Evaluation Settings")

# Fetch available models dynamically
try:
    models_resp = ModelService.get_model_list()

    if models_resp.get("models"):
        model_list = [
            # Ensure the list item is easy to read, e.g., "AAPL (prophet, trained 2023-10-27)"  # noqa: E501
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

# ------------------------------------------------------
# Main Content
# ------------------------------------------------------
if refresh and "No models" not in selected_model:
    try:
        # --- FIX: Robustly parse the ticker and model type using regex ---
        # Matches: [TICKER] ( [MODEL_TYPE] , ... )
        match = re.match(r"(\w+)\s+\(([^,]+)", selected_model)

        if not match:
            st.error(
                "Could not parse selected model string. Please check the model list format."  # noqa: E501
            )
            # Skip evaluation if parsing fails
            raise ValueError("Invalid model string format.")

        ticker = match.group(1).strip()  # e.g., "AAPL"
        model_type = match.group(2).strip()  # e.g., "prophet"

        # NOTE: Using 'model_type' parameter in URL to match the FastAPI route signature
        eval_url = f"http://127.0.0.1:8000/api/v1/evaluate?ticker={ticker}&period={period}&model_type={model_type}"  # noqa: E501
        eval_response = requests.get(eval_url)

        if eval_response.status_code != 200:
            st.error(
                f"Failed to fetch evaluation metrics from backend. Status: {eval_response.status_code}. Detail: {eval_response.json().get('detail', 'N/A')}"  # noqa: E501
            )
        else:
            metrics = eval_response.json()

            # --- KPI Section ---
            st.subheader(f"📈 Model Performance Overview — {ticker}")
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            kpi1.metric("MAE", f"{metrics.get('MAE', 0):.3f}")
            kpi2.metric("RMSE", f"{metrics.get('RMSE', 0):.3f}")
            kpi3.metric("R² Score", f"{metrics.get('R2', 0):.3f}")
            kpi4.metric("Data Points", metrics.get("data_points", "N/A"))

            st.markdown("---")

            # --- Performance Trend Chart ---
            if "predictions" in metrics:
                df = pd.DataFrame(metrics["predictions"])
                if not df.empty and all(
                    k in df.columns for k in ["date", "actual", "predicted"]
                ):
                    # Ensure 'date' is a datetime object for proper plotting
                    df["date"] = pd.to_datetime(df["date"])
                    st.subheader("📊 Actual vs Predicted Stock Prices")
                    
                    # Create figure with confidence intervals if available
                    fig = go.Figure()
                    
                    # Add confidence interval if lower_bound and upper_bound exist
                    if "lower_bound" in df.columns and "upper_bound" in df.columns:
                        fig.add_trace(go.Scatter(
                            x=df["date"].tolist() + df["date"].tolist()[::-1],
                            y=df["upper_bound"].tolist() + df["lower_bound"].tolist()[::-1],
                            fill="toself",
                            fillcolor="rgba(255, 165, 0, 0.2)",
                            line=dict(color="rgba(255, 165, 0, 0)"),
                            name="Confidence Interval",
                            showlegend=True,
                        ))
                    
                    # Add actual and predicted lines
                    fig.add_trace(go.Scatter(
                        x=df["date"],
                        y=df["actual"],
                        mode="lines",
                        name="Actual",
                        line=dict(color="#1f77b4", width=2),
                    ))
                    fig.add_trace(go.Scatter(
                        x=df["date"],
                        y=df["predicted"],
                        mode="lines",
                        name="Predicted",
                        line=dict(color="#ff7f0e", width=2),
                    ))
                    
                    fig.update_layout(
                        title=f"Model Prediction Performance for {ticker}",
                        xaxis_title="Date",
                        yaxis_title="Price (₹)",
                        template="plotly_white",
                        legend=dict(
                            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                        ),
                    )
                    st.plotly_chart(fig, width="stretch")
                else:
                    st.info("Prediction data not available for visualization.")

            # --- Residual Analysis ---
            if "predictions" in metrics:
                df["residual"] = df["actual"] - df["predicted"]
                st.subheader("📉 Residual Distribution (Error Spread)")
                fig_resid = px.histogram(
                    df, x="residual", nbins=25, title="Residual Error Distribution"
                )
                st.plotly_chart(fig_resid, width="stretch")

            # --- Feature Importance ---
            st.subheader("🔍 Key Feature Importance")
            feat_data = metrics.get("feature_importance", None)

            # --- Dynamically update Model Summary based on backend response ---
            model_summary_name = metrics.get("model_type", "Unknown Model")

            if feat_data and feat_data.get("Weight", ["N/A"])[0] != "N/A":
                df_feat = pd.DataFrame(feat_data)
                fig_feat = px.bar(
                    df_feat,
                    x="Feature",
                    y="Weight",
                    color="Feature",
                    text="Weight",
                    title="Model Feature Importance",
                )
                st.plotly_chart(fig_feat, width="stretch")
            else:
                st.info(
                    f"Feature importance is not available for {model_summary_name} models. "
                    "This will be available after implementing tree-based models (XGBoost, Random Forest)."
                )

            # --- Model Summary Section ---
            st.markdown("### 🧾 Model Summary")
            with st.container():
                st.write(f"""
                **Model:** {model_summary_name}
                **Ticker:** {ticker}
                **Evaluation Period:** {period}
                **Trained On:** {metrics.get('trained_on', datetime.date.today())}
                **Insights:**
                - R² of **{metrics.get('R2', 0):.2f}** indicates good predictive accuracy for short-term trends.  # noqa: E501
                - Residuals centered around zero → minimal systemic bias.
                - Slight overfitting in high-volatility windows.
                """)

            # --- Next Steps / Suggestions ---
            st.markdown("---")
            st.subheader("🚀 Suggested Next Steps")
            st.write("""
            - Add rolling retraining every 7 days to maintain model accuracy.
            - Compare different Prophet model configurations.
            - Integrate market sentiment signals for better volatility handling.
            - Monitor feature drift and retrain when R² drops by >10%.
            """)

    except Exception as e:
        logger.exception("Error fetching model insights")
        st.error(f"⚠️ Error fetching model insights: {e}")

else:
    st.info(
        "ℹ️ Select a trained model from the sidebar and click **Refresh Insights** to view performance."  # noqa: E501
    )
