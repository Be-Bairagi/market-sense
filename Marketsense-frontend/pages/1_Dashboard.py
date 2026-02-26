import logging

import altair as alt
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from services.dashboard_service import DashboardService

logger = logging.getLogger(__name__)


# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(page_title="MarketSense Dashboard", page_icon="📊", layout="wide")

# -----------------------------
# Header
# -----------------------------
st.title("📊 MarketSense Dashboard")

# -----------------------------
# Sidebar - Controls
# -----------------------------
st.sidebar.header("🔎 Stock Selection")

# Stock ticker input
ticker = st.sidebar.text_input("Enter Stock Ticker (e.g., AAPL, TSLA, MSFT):", "AAPL")

# Historical data period
period = st.sidebar.selectbox(
    "Select Historical Data Period:", ["7d", "30d", "90d", "180d"], index=1
)

# date interval for the period
interval = st.sidebar.selectbox(
    "Select Interval for the Period:", ["1d", "1hr", "1mo"], index=0
)

# Prediction horizon
predict_days = st.sidebar.slider("Prediction Days Ahead:", 1, 30, 10)

# Future option: model selection

model_type = st.sidebar.selectbox("Select Model (Future):", ["Prophet"], index=0)

st.sidebar.markdown("---")

# Action buttons
fetch_data_btn = st.sidebar.button("📊 Fetch Data")
predict_btn = st.sidebar.button("🤖 Run Prediction")

# -----------------------------
# Main Panel
# -----------------------------
if fetch_data_btn:
    try:
        response = DashboardService.fetch_stock_data(ticker, period, interval)
        if response.get("data"):
            data = response.get("data", [])
            df = pd.DataFrame(data)
            st.subheader(f"Historical Data for {ticker}")
            df_display = df.copy()
            df_display.index += 1

            # Mini chart for closing price trend
            chart = (
                alt.Chart(df)
                .mark_line()
                .encode(
                    x=alt.X("Date:T", title="Date"),
                    y=alt.Y(
                        "Close:Q",
                        title="Closing Price (USD)",
                        scale=alt.Scale(zero=False),
                    ),
                )
                .properties(height=250)
            )
            st.altair_chart(chart, width="stretch")

            st.dataframe(df_display)
        else:
            st.warning("⚠️ No historical data found from backend.")
    except Exception as e:
        logger.exception("Failed to fetch historical data from backend")
        st.error(f"❌ Failed to fetch historical data from backend: {e}")

if predict_btn:
    try:
        response = DashboardService.fetch_predictions(model_type, ticker, predict_days)
        if response:
            data = response
            predictions = data.get("predictions", [])
            metrics = data.get("metrics", {})

            df_pred = pd.DataFrame(predictions)

            # -----------------------------
            # Metrics Display
            # -----------------------------
            st.subheader("📈 Prediction Metrics")
            # col1, col2, col3 = st.columns(3)
            # col1.metric("Mean Absolute Error (MAE)", metrics.get("MAE", "N/A"))
            # col2.metric("Root Mean Squared Error (RMSE)", metrics.get("RMSE", "N/A"))
            # col3.metric("R² Score", metrics.get("R2", "N/A"))

            # -----------------------------
            # Prediction Line Chart
            # -----------------------------
            # st.subheader("📊 Predicted Prices")
            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=df_pred["Date"],
                    y=df_pred["Predicted"],
                    mode="lines",
                    name="Predicted",
                    line=dict(color="orange", width=2, dash="dot"),
                )
            )

            fig.update_layout(
                title=f"{ticker} Stock Price Prediction",
                xaxis_title="Date",
                yaxis_title="Price (USD)",
                template="plotly_white",
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                ),
            )
            st.plotly_chart(fig, width="stretch")

            # -----------------------------
            # Prediction Table
            # -----------------------------
            st.subheader(f"🤖 Predictions for {ticker} - Next {predict_days} Days")
            st.write(df_pred)

            # -----------------------------
            # Next-Day Prediction Summary
            # -----------------------------
            next_day = df_pred.iloc[-1]
            st.markdown(
                f"**Next Predicted Closing Price:** ${next_day['Predicted']:.2f}"
            )

            # -----------------------------
            # Export Options
            # -----------------------------
            csv = df_pred.to_csv(index=False).encode()
            st.download_button(
                label="Download Predictions CSV",
                data=csv,
                file_name=f"{ticker}_predictions.csv",
                mime="text/csv",
            )
        else:
            st.error("❌ Failed to fetch predictions from backend.")
    except Exception as e:
        logger.exception("Error fetching predictions")
        st.error(f"⚠️ Error fetching predictions: {e}")

if not fetch_data_btn and not predict_btn:
    st.info(
        "ℹ️ Enter parameters in the sidebar and click **Fetch Data** or **Run Prediction** to get started."  # noqa: E501
    )
