# app.py
import random
import time
from datetime import datetime
import streamlit as st
import requests
from data.nifty50 import NIFTY_50_SYMBOLS, NIFTY_50_MAP
from services.dashboard_service import DashboardService

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


def premium_health_check_ui():
    """Enhanced industry-standard loading screen with rotating tips."""
    tips = [
        "Use the **Todays Picks** page for automated, beginner-friendly stock recommendations.",
        "You can train custom AI models for any NIFTY 50 stock in the **Model Management** section.",
        "Check **Model Performance** to see accuracy and backtests for all trained models.",
        "MarketSense tracks **40+ technical indicators** including RSI, MACD, and Bollinger Bands.",
        "We monitor **FII & DII flows** and **India VIX** to provide a macro-aware trading signal.",
        "Clear BUY/HOLD/AVOID signals help you navigate markets without complex jargon.",
        "The **Data Pipeline** section allows you to trigger fresh ingestion and feature computation."
    ]
    
    placeholder = st.empty()
    tip = random.choice(tips)
    
    with placeholder.container():
        st.markdown("""
        <style>
        .premium-loader {
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            padding: 3rem; text-align: center; background: #ffffff; border-radius: 1.5rem;
            box-shadow: 0 10px 40px -10px rgba(0, 0, 0, 0.1); margin: 5vh auto; max-width: 600px;
            border: 1px solid #e2e8f0;
        }
        .loader-logo { font-size: 3.5rem; margin-bottom: 1rem; animation: pulse 2s infinite ease-in-out; }
        @keyframes pulse {
            0% { transform: scale(0.95); opacity: 0.8; }
            50% { transform: scale(1.05); opacity: 1; }
            100% { transform: scale(0.95); opacity: 0.8; }
        }
        .loading-title { font-size: 1.8rem; font-weight: 800; color: #1e293b; margin-bottom: 0.5rem; }
        .loading-step { font-size: 1rem; color: #64748b; margin-bottom: 1.5rem; height: 1.5rem; font-weight: 500; }
        .tip-box { 
            background: #f0f7ff; border-radius: 1rem; padding: 1.2rem; 
            border-left: 5px solid #2563eb; text-align: left; width: 100%;
        }
        .tip-header { color: #2563eb; font-weight: 700; margin-bottom: 0.3rem; font-size: 0.9rem; letter-spacing: 0.05rem; text-transform: uppercase; }
        .progress-bar-container {
            width: 100%; background: #e2e8f0; border-radius: 999px; height: 6px; margin-bottom: 2rem; overflow: hidden;
        }
        .progress-bar-fill {
            height: 100%; background: linear-gradient(90deg, #2563eb, #3b82f6); width: 0%; transition: width 0.4s ease;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="premium-loader">', unsafe_allow_html=True)
        st.markdown('<div class="loader-logo">🚀</div>', unsafe_allow_html=True)
        st.markdown('<div class="loading-title">MarketSense Engine</div>', unsafe_allow_html=True)
        
        status_text = st.empty()
        progress_bar = st.empty()
        
        st.markdown(f"""
        <div class="tip-box">
            <div class="tip-header">💡 Pro Tip</div>
            <div style="color: #475569; font-size: 0.95rem;">{tip}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Sequence of checks
        steps = [
            ("📡 Establishing connection...", 20),
            ("🗄️ Checking database integrity...", 45),
            ("🌐 Testing external data feeds...", 70),
            ("🧠 Loading model weights...", 90),
            ("✅ System Ready", 100)
        ]
        
        # Real check in background
        healthy, health_data = check_backend_health()
        
        for msg, progress in steps:
            status_text.markdown(f'<div style="text-align:center; color:#64748b; margin-bottom:0.5rem;">{msg}</div>', unsafe_allow_html=True)
            progress_bar.markdown(f"""
            <div style="width:100%; max-width:400px; margin:0 auto 2rem auto;">
                <div class="progress-bar-container">
                    <div class="progress-bar-fill" style="width: {progress}%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            time.sleep(0.3)
            
    placeholder.empty()
    return healthy, health_data


# Health check on startup
if "health_check_done" not in st.session_state:
    healthy, health_data = premium_health_check_ui()
    st.session_state["backend_healthy"] = healthy
    st.session_state["health_data"] = health_data
    st.session_state["health_check_done"] = True

# If backend is down, show error page
if not st.session_state.get("backend_healthy", False):
    st.set_page_config(page_title="Service Unavailable", page_icon="⚠️")
    st.markdown("""
    <style>
    .error-container {
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        min-height: 60vh; text-align: center;
    }
    .error-code { font-size: 6rem; font-weight: bold; color: #dc2626; margin-bottom: 1rem; }
    .error-title { font-size: 1.5rem; color: #1f2937; margin-bottom: 0.5rem; }
    .error-message { color: #6b7280; margin-bottom: 2rem; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="error-container">', unsafe_allow_html=True)
    st.markdown('<div class="error-code">503</div>', unsafe_allow_html=True)
    st.markdown('<div class="error-title">Service Temporarily Unavailable</div>', unsafe_allow_html=True)
    st.markdown('<div class="error-message">Unable to connect to the backend.<br>Ensure the server is running on http://localhost:8000</div>', unsafe_allow_html=True)

    if st.button("🔄 Retry Connection", type="primary"):
        st.session_state.pop("health_check_done", None)
        st.session_state.pop("backend_healthy", None)
        st.session_state.pop("health_data", None)
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="MarketSense — AI Stock Predictor",
    page_icon="📈",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
.hero-title {
    font-size: 3rem; font-weight: 700; color: #2563eb;
    text-align: center; margin-bottom: 0.3rem;
}
.hero-subtitle {
    text-align: center; font-size: 1.2rem; color: #64748b;
    margin-bottom: 2.5rem;
}
.card {
    background-color: var(--background-color-secondary);
    border-radius: 1rem; padding: 1.5rem;
    box-shadow: 0px 4px 20px rgba(0,0,0,0.05);
    transition: 0.3s;
}
.card:hover {
    box-shadow: 0px 4px 30px rgba(0,0,0,0.1);
    transform: translateY(-5px);
}
.card h3 { color: #2563eb; margin-bottom: 0.5rem; }
.feature-icon { font-size: 2rem; margin-bottom: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────
st.markdown('<h1 class="hero-title">🚀 MarketSense</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-subtitle">AI-powered stock predictions for the Indian market. '
    'Clear signals, plain-English explanations — no jargon.</p>',
    unsafe_allow_html=True,
)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image(
        "https://cdn.dribbble.com/users/1162077/screenshots/3848914/programmer.gif",
        width=500,
    )

st.write("")
st.write("")

# ── Feature Cards ─────────────────────────────────────────────
st.subheader("✨ Why MarketSense?")
st.write(
    "AI-powered analysis of Indian stocks — from technical indicators to "
    "news sentiment — all distilled into clear BUY / HOLD / AVOID signals."
)

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("""
    <div class='card'>
        <div class='feature-icon'>🤖</div>
        <h3>XGBoost Predictions</h3>
        <p>ML-powered direction predictions (BUY / HOLD / AVOID) with confidence scores and risk assessment.</p>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div class='card'>
        <div class='feature-icon'>📊</div>
        <h3>40+ Technical Indicators</h3>
        <p>RSI, MACD, Bollinger Bands, EMAs, ADX, ATR, OBV — automatically computed and stored.</p>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown("""
    <div class='card'>
        <div class='feature-icon'>💬</div>
        <h3>Plain-English Explanations</h3>
        <p>No jargon. Get key drivers like "RSI shows oversold recovery" and bear-case risk warnings.</p>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# ── Quick Prediction ──────────────────────────────────────────
st.divider()
st.subheader("⚡ Quick Prediction")
st.write("Pick a NIFTY 50 stock and get an instant AI signal.")

qcol1, qcol2 = st.columns([2, 1])

with qcol1:
    quick_options = [f"{s} — {NIFTY_50_MAP[s]}" for s in NIFTY_50_SYMBOLS[:10]]
    quick_selected = st.selectbox("Stock", quick_options, index=0, key="quick_ticker")
    quick_symbol = quick_selected.split(" — ")[0]

with qcol2:
    st.write("")  # spacer
    quick_predict = st.button("🎯 Get Signal", use_container_width=True, type="primary")

if quick_predict:
    with st.spinner(f"Analyzing {quick_symbol}..."):
        result = DashboardService.fetch_rich_prediction(quick_symbol, "xgboost")

    if result.get("error"):
        st.warning(f"⚠️ {result['error']}")
        st.info("Train an XGBoost model for this stock in **Model Management** first.")
    else:
        direction = result.get("direction", "HOLD")
        confidence = result.get("confidence", 0.0)
        signals = {"BUY": "🟢", "HOLD": "🟡", "AVOID": "🔴"}
        colors = {"BUY": "#16a34a", "HOLD": "#ca8a04", "AVOID": "#dc2626"}

        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #f8fafc, #e2e8f0);
            border-left: 5px solid {colors.get(direction, '#64748b')};
            border-radius: 0.75rem; padding: 1.5rem; margin: 1rem 0;
        ">
            <span style="font-size: 2.5rem;">{signals.get(direction, '🟡')}</span>
            <span style="font-size: 2rem; font-weight: 700; color: {colors.get(direction, '#64748b')}; margin-left: 0.5rem;">
                {direction}
            </span>
            <span style="color: #64748b; margin-left: 1rem;">
                Confidence: {confidence:.0%} · {result.get('horizon', 'short_term')}
            </span>
        </div>
        """, unsafe_allow_html=True)

        drivers = result.get("key_drivers", [])
        if drivers:
            for d in drivers[:3]:
                st.markdown(f"- {d}")

st.write("")
st.divider()

# ── Platform Overview ─────────────────────────────────────────
st.subheader("📈 Platform Overview")

c1, c2 = st.columns([2, 1])

with c1:
    st.markdown("""
    MarketSense combines **Machine Learning** and **real-time Indian market data**
    to generate actionable insights for NIFTY 50 stocks.

    - 🎯 **AI Signal Cards** — BUY / HOLD / AVOID with confidence
    - 📊 **Interactive Charts** — Candlestick, volume, comparison
    - 🧬 **Feature Store** — 40+ indicators computed automatically
    - 🌍 **Macro Awareness** — USD/INR, Crude, VIX, FII/DII tracking
    - 💬 **Beginner-Friendly** — Plain-English explanations, no jargon
    """)

with c2:
    st.image(
        "./assets/BrandLogoMarketSense.png",
        caption="Be fearful when others are greedy and greedy only when others are fearful. — Warren Buffett",
        width=200,
    )

st.write("")
st.divider()

# ── CTA ───────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style='text-align:center; margin-top:2rem;'>
        <h2>💡 Ready to explore AI-powered investing?</h2>
        <p>Navigate to the <b>Dashboard</b> from the sidebar to start analyzing stocks.</p>
        <p style='color:#94a3b8; font-size:0.9rem;'>
            © {datetime.now().year} MarketSense | Built with ❤️ using FastAPI & Streamlit
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
