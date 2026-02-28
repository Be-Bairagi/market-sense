# app.py
from datetime import datetime

import requests
import streamlit as st

# Backend configuration
BACKEND_URL = "http://localhost:8000"
HEALTH_ENDPOINT = f"{BACKEND_URL}/health"


def check_backend_health():
    """Check if backend is available."""
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        if response.status_code == 200:
            return True, response.json()
        return False, None
    except Exception:
        return False, None


# Health check on startup
if "health_check_done" not in st.session_state:
    # Show loading in titlebar
    with st.spinner("Checking backend services..."):
        healthy, health_data = check_backend_health()
    st.session_state["backend_healthy"] = healthy
    st.session_state["health_data"] = health_data
    st.session_state["health_check_done"] = True

# If backend is down, show error page and stop
if not st.session_state.get("backend_healthy", False):
    st.set_page_config(page_title="Service Unavailable", page_icon="⚠️")
    st.markdown("""
    <style>
    .error-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 60vh;
        text-align: center;
    }
    .error-code {
        font-size: 6rem;
        font-weight: bold;
        color: #dc2626;
        margin-bottom: 1rem;
    }
    .error-title {
        font-size: 1.5rem;
        color: #1f2937;
        margin-bottom: 0.5rem;
    }
    .error-message {
        color: #6b7280;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="error-container">', unsafe_allow_html=True)
    st.markdown('<div class="error-code">503</div>', unsafe_allow_html=True)
    st.markdown('<div class="error-title">Service Temporarily Unavailable</div>', unsafe_allow_html=True)
    st.markdown('<div class="error-message">Unable to connect to the backend service.<br>Please ensure the backend server is running on http://localhost:8000</div>', unsafe_allow_html=True)
    
    if st.button("🔄 Retry Connection", type="primary"):
        # Clear health check state to re-attempt
        st.session_state.pop("health_check_done", None)
        st.session_state.pop("backend_healthy", None)
        st.session_state.pop("health_data", None)
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# Page config
st.set_page_config(
    page_title="MarketSense — AI Stock Predictor",
    page_icon="📈",
    layout="wide",
)

# --- Hero Section ---
st.markdown(
    """
    <style>
    .hero-title {
        font-size: 3rem;
        font-weight: 700;
        color: #2563eb;
        text-align: center;
        margin-bottom: 0.3rem;
    }
    .hero-subtitle {
        text-align: center;
        font-size: 1.2rem;
        color: #64748b;
        margin-bottom: 2.5rem;
    }
    .card {
        background-color: var(--background-color-secondary);
        border-radius: 1rem;
        padding: 1.5rem;
        box-shadow: 0px 4px 20px rgba(0,0,0,0.05);
        transition: 0.3s;
    }
    .card:hover {
        box-shadow: 0px 4px 30px rgba(0,0,0,0.1);
        transform: translateY(-5px);
    }
    .card h3 {
        color: #2563eb;
        margin-bottom: 0.5rem;
    }
    .feature-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<h1 class="hero-title">🚀 MarketSense</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-subtitle">AI-driven insights and stock market forecasting for smarter investing decisions.</p>',  # noqa: E501
    unsafe_allow_html=True,
)

# --- Introduction / Hero Image (optional) ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image(
        "https://cdn.dribbble.com/users/1162077/screenshots/3848914/programmer.gif",
        width=500,
    )

st.write("")
st.write("")

# --- Feature Cards ---
st.subheader("✨ Why MarketSense?")
st.write(
    "Leverage Artificial Intelligence to uncover stock patterns, trends, and insights — all in one sleek dashboard."  # noqa: E501
)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        <div class='card'>
            <div class='feature-icon'>🤖</div>
            <h3>AI-Powered Predictions</h3>
            <p>Train machine learning models like Linear Regression, LSTM, and Prophet to forecast real stock trends.</p>  # noqa: E501
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div class='card'>
            <div class='feature-icon'>📊</div>
            <h3>Interactive Analytics</h3>
            <p>Visualize actual vs predicted prices with advanced charts and compare model accuracy in real time.</p>  # noqa: E501
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
        <div class='card'>
            <div class='feature-icon'>🌍</div>
            <h3>Scalable & Modular</h3>
            <p>Built with FastAPI + Streamlit, designed for seamless scalability and integration with real market data sources.</p>  # noqa: E501
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")
st.divider()

# --- Live System Overview ---
st.subheader("📈 Platform Overview")

c1, c2, c3 = st.columns([2, 1, 1])

with c1:
    st.markdown("""
        MarketSense combines the power of **Machine Learning** and **real-time financial data**  # noqa: E501
        to generate actionable insights.

        In this dashboard, you can:
        - Select your stock ticker and period
        - Train AI models instantly
        - Validate model performance using MAE, RMSE, and R²
        - Visualize predicted vs actual prices interactively

        This tool is designed to be **academic-grade + industry-ready**, perfect for both research and deployment.  # noqa: E501
        """)

with c3:
    st.image(
        "./assets\\BrandLogoMarketSense.png",
        caption="Be fearful when others are greedy and greedy only when others are fearful. - Warren Buffett",  # noqa: E501
        width=200,
    )


st.write("")
st.divider()

# --- CTA Section ---
st.markdown(
    f"""
    <div style='text-align:center; margin-top:2rem;'>
        <h2>💡 Ready to explore the future of AI investing?</h2>
        <p>Navigate to the <b>Dashboard</b> from the sidebar and start predicting today.</p>  # noqa: E501
        <p style='color:#94a3b8; font-size:0.9rem;'>© {datetime.now().year} MarketSense | Built with ❤️ using FastAPI & Streamlit</p>  # noqa: E501
    </div>
    """,
    unsafe_allow_html=True,
)
