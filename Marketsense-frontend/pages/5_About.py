from datetime import date

import streamlit as st

# --------------------------------
# Page Config
# --------------------------------
st.set_page_config(
    page_title="About & Help - MarketSense", page_icon="ℹ️", layout="wide"
)

# --------------------------------
# Header
# --------------------------------
st.title("ℹ️ About & Help")
st.markdown(
    "Welcome to **MarketSense** — your AI-powered stock prediction companion 🚀"
)

# --------------------------------
# About Section
# --------------------------------
st.header("📘 About MarketSense")
st.write("""
MarketSense is an **AI-driven stock market prediction tool** built to analyze historical data and forecast future stock trends.  # noqa: E501
It leverages **machine learning algorithms** (currently Prophet, future support for LSTM and XGBoost)  # noqa: E501
to provide insightful, data-backed predictions that assist traders, researchers, and analysts in decision-making.  # noqa: E501

This project is developed as part of the **M.Tech Final Year Major Project** under **MAKAUT University**,  # noqa: E501
showcasing an industry-standard architecture using **FastAPI** (Backend) and **Streamlit** (Frontend).  # noqa: E501
""")

st.markdown("---")

# --------------------------------
# How It Works Section
# --------------------------------
st.header("⚙️ How It Works")

col1, col2 = st.columns([1, 1])

with col1:
    st.image(
        "https://cdn-icons-png.flaticon.com/512/6821/6821228.png",
        caption="AI Model Pipeline",
        width=250,
    )

with col2:
    st.markdown("""
    MarketSense follows a clear and modular workflow:
    1. **Data Fetching:** Stock data is fetched from Yahoo Finance using `yfinance`.
    2. **Preprocessing:** Handles missing values and prepares structured input for the model.  # noqa: E501
    3. **Model Training:** Uses Prophet for baseline predictions (extendable to LSTM, Random Forest, etc.).  # noqa: E501
    4. **Prediction:** Provides price forecasts and performance metrics (MAE, RMSE, R²).
    5. **Visualization:** Displays charts and insights through the Streamlit dashboard.
    """)

st.markdown("---")

# --------------------------------
# How to Use
# --------------------------------
st.header("🧭 How to Use MarketSense")
st.write("""
1. **Go to the Dashboard Page.**
   Enter the stock ticker symbol (like `AAPL`, `GOOG`, `INFY.NS`) and select a date range.  # noqa: E501
2. **Click “Run Prediction.”**
   MarketSense will train the model and generate predictions.
3. **View Model Insights.**
   Check performance metrics and charts comparing predicted vs actual values.
4. **Manage Models.**
   Use the Settings Page to retrain or delete models.
""")

st.success(
    "💡 Tip: Start with well-known tickers (like AAPL or MSFT) for best results."
)

st.markdown("---")

# --------------------------------
# FAQs Section
# --------------------------------
st.header("❓ FAQs & Troubleshooting")

faq_expander = st.expander("Click to view common questions")

with faq_expander:
    st.markdown("""
    **Q1. Why is my prediction taking long?**
    The app retrains the model on the latest data each time.
    Consider limiting your date range for faster results.

    **Q2. I see 'Failed to fetch data' errors.**
    Ensure your backend (FastAPI) server is running at `http://127.0.0.1:8000`.

    **Q3. Can I add my own model?**
    Yes! MarketSense is modular. Add your model in `backend/models/` and register it in `train.py`.  # noqa: E501

    **Q4. Does this app use real-time stock data?**
    Currently, it fetches end-of-day data. Future versions will support real-time feeds.
    """)

st.markdown("---")

# --------------------------------
# Contact / Support
# --------------------------------
st.header("📩 Contact & Support")

col1, col2 = st.columns([1, 2])
with col1:
    st.image(
        "https://cdn-icons-png.flaticon.com/512/5968/5968705.png",
        caption="Contact Developer",
        width=150,
    )

with col2:
    st.markdown(f"""
    **Developer:** Brotati Bairagi
    **Project:** M.Tech Final Year - MarketSense
    **Institution:** MAKAUT University
    **Email:** [brotati.bairagi@example.com](mailto:brotati.bairagi@example.com)
    **GitHub:** [github.com/brotati-bairagi](https://github.com/brotati-bairagi)
    **Version:** 1.0.0
    **Last Updated:** {date.today().strftime('%Y-%m-%d')}
    """)

st.info("Need help? Reach out via email or open an issue on GitHub!")

st.markdown("---")

st.caption("© 2025 MarketSense | Built with ❤️ using FastAPI + Streamlit")
