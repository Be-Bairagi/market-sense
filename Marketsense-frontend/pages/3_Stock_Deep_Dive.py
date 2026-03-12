import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

from services.dashboard_service import DashboardService
from utils.helpers import format_currency, get_sentiment_color, get_signal_icon

# Page configuration
st.set_page_config(
    page_title="Stock Deep Dive | MarketSense",
    page_icon="📈",
    layout="wide"
)

# Custom CSS for premium look
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        border: 1px solid #e9ecef;
    }
    .bear-case-box {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .explain-box {
        background-color: #e7f3ff;
        border-left: 5px solid #007bff;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .sentiment-tag {
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #007bff;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

def load_all_data(symbol):
    """Fetch all necessary data concurrently for better performance."""
    with ThreadPoolExecutor(max_workers=4) as executor:
        f_profile = executor.submit(DashboardService.fetch_stock_profile, symbol)
        f_news = executor.submit(DashboardService.fetch_stock_news, symbol)
        f_accuracy = executor.submit(DashboardService.fetch_stock_accuracy, symbol)
        f_prices = executor.submit(DashboardService.fetch_stock_data, symbol, "6mo", "1d")
        
        return {
            "profile": f_profile.result(),
            "news": f_news.result(),
            "accuracy": f_accuracy.result(),
            "prices": f_prices.result()
        }

def render_prediction_tab(symbol, model_type, horizon_label):
    """Render a specific prediction horizon tab."""
    prediction = DashboardService.fetch_rich_prediction(symbol, model_type=model_type)
    
    if not isinstance(prediction, dict) or "error" in prediction:
        err = prediction.get("error", "Unknown error") if isinstance(prediction, dict) else "Invalid response"
        st.error(f"Failed to fetch {horizon_label} prediction: {err}")
        return

    pred_data = prediction.get("predictions", {})
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.markdown("### 🚦 Signal")
        signal = pred_data.get("direction", "HOLD").upper()
        icon = get_signal_icon(signal)
        st.subheader(f"{icon} {signal}")
        
        conf = pred_data.get("confidence", 0)
        st.write(f"Confidence: **{conf}%**")
        st.progress(conf / 100)

    with col2:
        st.markdown("### 🎯 Targets")
        st.write(f"**Entry Zone:** {format_currency(pred_data.get('target_low', 0))} - {format_currency(pred_data.get('target_high', 0))}")
        st.write(f"**Stop Loss:** :red[{format_currency(pred_data.get('stop_loss', 0))}]")
        
    with col3:
        st.markdown("### ⏳ Validity")
        valid_until = pred_data.get("valid_until", "N/A")
        st.write(f"Valid Until: **{valid_until}**")
        st.write(f"Horizon: **{horizon_label}**")

    st.divider()
    
    # Explain Item
    st.markdown("#### 💡 Explain this to me")
    drivers = pred_data.get("key_drivers", [])
    if drivers:
        for driver in drivers[:3]:
            st.markdown(f"• {driver}")
    else:
        st.write("No major drivers identified for this horizon.")
        
    # Bear Case
    st.markdown("#### ⚠️ Bear Case (Risks)")
    bear_case = pred_data.get("bear_case", "No significant risks identified.")
    st.markdown(f'<div class="bear-case-box">{bear_case}</div>', unsafe_allow_html=True)

def render_price_chart(price_data, symbol):
    """Render the Plotly price chart."""
    if not price_data or "data" not in price_data:
        st.warning("Historical price data unavailable.")
        return

    df = pd.DataFrame(price_data["data"])
    df["Date"] = pd.to_datetime(df["Date"])
    
    fig = go.Figure()
    
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df['Date'],
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Historical'
    ))
    
    fig.update_layout(
        title=f"{symbol} Price Action (Last 6 Months)",
        xaxis_rangeslider_visible=False,
        height=500,
        margin=dict(l=0, r=0, t=30, b=0),
        template="plotly_white"
    )
    
    st.plotly_chart(fig, use_container_width=True)

def main():
    # Attempt to get symbol from query params (e.g. from Today's Picks)
    query_params = st.query_params
    symbol = query_params.get("symbol", "RELIANCE.NS")
    
    # Sidebar Search
    st.sidebar.title("🔍 Search")
    new_symbol = st.sidebar.text_input("Enter Ticker (e.g. INFY.NS)", value=symbol).upper()
    
    if new_symbol != symbol:
        st.query_params["symbol"] = new_symbol
        st.rerun()

    # Load Data
    with st.spinner(f"Fetching intelligence for {symbol}..."):
        data = load_all_data(symbol)

    profile = data["profile"]
    
    # Header
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        company_name = profile.get("company_name", symbol)
        sector = profile.get("sector", "General")
        st.title(f"{company_name} ({symbol})")
        st.markdown(f"**Sector:** {sector} | **Industry:** {profile.get('industry', 'N/A')}")
    
    with col_h2:
        mcap = profile.get("market_cap", 0)
        if mcap:
            st.metric("Market Cap", f"₹{mcap/1e7:.1f} Cr")
        else:
            st.metric("Market Cap", "N/A")

    st.divider()

    # Main Tabs
    tab_signal, tab_news, tab_accuracy = st.tabs(["🎯 AI Signals", "📰 News & Sentiment", "📊 Historical Accuracy"])

    with tab_signal:
        horizon_tabs = st.tabs(["Short-term (1-5d)", "Swing (1-4w)", "Long-term (Months)"])
        
        with horizon_tabs[0]:
            render_prediction_tab(symbol, "xgboost", "Short-term")
            
        with horizon_tabs[1]:
            # For MVP, we might use prophet for longer horizons or just xgboost
            render_prediction_tab(symbol, "prophet", "Swing")
            
        with horizon_tabs[2]:
            st.info("Long-term model integration in progress.")

        st.divider()
        render_price_chart(data["prices"], symbol)

    with tab_news:
        st.subheader("Market Sentiment Timeline")
        news = data["news"]
        
        if isinstance(news, list) and len(news) > 0:
            for item in news:
                col_n1, col_n2 = st.columns([1, 10])
                with col_n1:
                    st.markdown(f"### {item['icon']}")
                with col_n2:
                    st.markdown(f"**{item['headline']}**")
                    st.caption(f"{item['published_at']} | Sentiment: {item['sentiment'].capitalize()} ({item['score']})")
                st.divider()
        else:
            st.info("No recent news found for this ticker.")

    with tab_accuracy:
        st.subheader("System Reliability Tracker")
        accuracy = data["accuracy"]
        
        if not isinstance(accuracy, dict) or "error" in accuracy:
            st.info("Performance metrics currently unavailable for this stock.")
        else:
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                st.metric("Ticker Win Rate", f"{accuracy.get('win_rate', 0)}%")
            with col_a2:
                st.metric("Total Predictions", accuracy.get("total_samples", 0))
                
            history = accuracy.get("history", [])
            if history:
                df_hist = pd.DataFrame(history)
                df_hist.columns = ["Date", "Horizon", "Direction", "Conf %", "Outcome", "Model"]
                st.table(df_hist)
            else:
                st.info("No prediction history available for this stock yet.")

if __name__ == "__main__":
    main()
