import logging

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from services.dashboard_service import DashboardService

logger = logging.getLogger(__name__)


# -----------------------------
# Session State for Data Refresh
# -----------------------------
if 'last_updated' not in st.session_state:
    st.session_state.last_updated = None
if 'current_data' not in st.session_state:
    st.session_state.current_data = None
if 'current_ticker' not in st.session_state:
    st.session_state.current_ticker = None
if 'refresh_trigger' not in st.session_state:
    st.session_state.refresh_trigger = 0

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

# Stock comparison - multi-select
compare_tickers = st.sidebar.multiselect(
    "Compare Stocks (select multiple):",
    ["AAPL", "TSLA", "MSFT", "GOOGL", "AMZN", "NVDA", "META"],
    default=[]
)

# Single stock ticker (for primary view)
if compare_tickers:
    ticker = st.sidebar.selectbox("Primary Stock:", compare_tickers, index=0)
else:
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

# -----------------------------
# Real-time Refresh Controls
# -----------------------------
st.sidebar.header("🔄 Data Refresh")

# Auto-refresh interval
refresh_interval = st.sidebar.selectbox(
    "Auto-refresh interval:",
    ["Manual only", "30 seconds", "1 minute", "5 minutes"],
    index=0
)

# Refresh button
refresh_btn = st.sidebar.button("🔄 Refresh Data")

# Auto-refresh logic based on interval
if refresh_interval != "Manual only":
    interval_seconds = {"30 seconds": 30, "1 minute": 60, "5 minutes": 300}
    time_since_update = 0
    if st.session_state.last_updated:
        time_since_update = (pd.Timestamp.now() - st.session_state.last_updated).total_seconds()
    
    if time_since_update >= interval_seconds.get(refresh_interval, 0):
        st.session_state.refresh_trigger += 1
        st.rerun()

# Last updated timestamp display
if st.session_state.last_updated:
    st.sidebar.markdown(f"**Last updated:** {st.session_state.last_updated.strftime('%H:%M:%S')}")
else:
    st.sidebar.markdown("_No data loaded yet_")

st.sidebar.markdown("---")

# Action buttons
fetch_data_btn = st.sidebar.button("📊 Fetch Data")
predict_btn = st.sidebar.button("🤖 Run Prediction")

# -----------------------------
# Main Panel
# -----------------------------

# Check if we should fetch data (button click or refresh trigger)
should_fetch = fetch_data_btn or refresh_btn or st.session_state.refresh_trigger > 0

# Reset refresh trigger after handling
if st.session_state.refresh_trigger > 0 and not fetch_data_btn:
    st.session_state.refresh_trigger = 0

if should_fetch:
    # Loading indicator
    with st.spinner(f"Loading {ticker} data..."):
        try:
            # Determine which tickers to fetch
            tickers_to_fetch = compare_tickers if compare_tickers else [ticker]
            
            all_data = {}
            for t in tickers_to_fetch:
                response = DashboardService.fetch_stock_data(t, period, interval)
                if response.get("data"):
                    all_data[t] = pd.DataFrame(response.get("data", []))
            
            if all_data:
                # Update session state
                st.session_state.current_data = all_data
                st.session_state.current_ticker = ticker
                st.session_state.last_updated = pd.Timestamp.now()
                
                # Display stock comparison if multiple tickers
                if len(tickers_to_fetch) > 1:
                    st.subheader(f"📊 Stock Comparison: {', '.join(tickers_to_fetch)}")
                    
                    # Create comparison candlestick charts
                    for t in tickers_to_fetch:
                        df = all_data[t]
                        if 'Date' in df.columns and all(col in df.columns for col in ['Open', 'High', 'Low', 'Close']):
                            fig = go.Figure(data=[
                                go.Candlestick(
                                    x=df['Date'],
                                    open=df['Open'],
                                    high=df['High'],
                                    low=df['Low'],
                                    close=df['Close'],
                                    name=t
                                )
                            ])
                            
                            fig.update_layout(
                                title=f"{t} - Candlestick Chart",
                                xaxis_title="Date",
                                yaxis_title="Price (USD)",
                                template="plotly_white",
                                xaxis_rangeslider_visible=False,
                                height=400
                            )
                            st.plotly_chart(fig, use_container_width=True)
                    
                    # Comparison line chart for all tickers
                    fig_compare = go.Figure()
                    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']
                    
                    for i, t in enumerate(tickers_to_fetch):
                        df = all_data[t]
                        if 'Date' in df.columns and 'Close' in df.columns:
                            fig_compare.add_trace(go.Scatter(
                                x=df['Date'],
                                y=df['Close'],
                                mode='lines',
                                name=t,
                                line=dict(color=colors[i % len(colors)], width=2)
                            ))
                    
                    fig_compare.update_layout(
                        title="Price Comparison - Close Prices",
                        xaxis_title="Date",
                        yaxis_title="Price (USD)",
                        template="plotly_white",
                        height=350
                    )
                    st.plotly_chart(fig_compare, use_container_width=True)
                
                else:
                    # Single stock view with candlestick and volume
                    t = ticker
                    df = all_data[t]
                    
                    st.subheader(f"📈 {t} - Interactive Chart")
                    
                    # Candlestick chart with OHLC data
                    if all(col in df.columns for col in ['Open', 'High', 'Low', 'Close']):
                        fig_candle = go.Figure(data=[
                            go.Candlestick(
                                x=df['Date'],
                                open=df['Open'],
                                high=df['High'],
                                low=df['Low'],
                                close=df['Close'],
                                name='OHLC',
                                increasing_line_color='#26a69a',
                                decreasing_line_color='#ef5350'
                            )
                        ])
                        
                        fig_candle.update_layout(
                            title=f"{t} - Candlestick Chart",
                            xaxis_title="Date",
                            yaxis_title="Price (USD)",
                            template="plotly_white",
                            xaxis_rangeslider_visible=False,
                            height=400,
                            hovermode="x unified"
                        )
                        st.plotly_chart(fig_candle, use_container_width=True)
                    
                    # Volume bar chart
                    if 'Volume' in df.columns:
                        fig_volume = go.Figure(data=[
                            go.Bar(
                                x=df['Date'],
                                y=df['Volume'],
                                name='Volume',
                                marker_color='rgba(100, 149, 237, 0.6)'
                            )
                        ])
                        
                        fig_volume.update_layout(
                            title=f"{t} - Trading Volume",
                            xaxis_title="Date",
                            yaxis_title="Volume",
                            template="plotly_white",
                            height=250,
                            hovermode="x unified"
                        )
                        st.plotly_chart(fig_volume, use_container_width=True)
                
                # Display data table
                st.subheader(f"📋 Historical Data for {ticker}")
                for t, df in all_data.items():
                    df_display = df.copy()
                    df_display.index += 1
                    with st.expander(f"View {t} data"):
                        st.dataframe(df_display, use_container_width=True)
                
                # Show last updated time
                st.caption(f"🕐 Last updated: {st.session_state.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
                
            else:
                st.warning("⚠️ No historical data found from backend.")
        except Exception as e:
            logger.exception("Failed to fetch historical data from backend")
            st.error(f"❌ Failed to fetch historical data from backend: {e}")

# Use the primary ticker for predictions (from comparison selection if available)
prediction_ticker = compare_tickers[0] if compare_tickers else ticker

if predict_btn:
    try:
        response = DashboardService.fetch_predictions(model_type, prediction_ticker, predict_days)
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
                title=f"{prediction_ticker} Stock Price Prediction",
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
            st.subheader(f"🤖 Predictions for {prediction_ticker} - Next {predict_days} Days")
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
                file_name=f"{prediction_ticker}_predictions.csv",
                mime="text/csv",
            )
        else:
            st.error("❌ Failed to fetch predictions from backend.")
    except Exception as e:
        logger.exception("Error fetching predictions")
        st.error(f"⚠️ Error fetching predictions: {e}")

if not fetch_data_btn and not predict_btn and not refresh_btn and st.session_state.refresh_trigger == 0:
    st.info(
        "ℹ️ Enter parameters in the sidebar and click **Fetch Data**, **Run Prediction**, or **Refresh Data** to get started. Use the auto-refresh option for automatic updates."  # noqa: E501
    )
