# app.py
import random
import time
from datetime import datetime
import streamlit as st
from data.nifty50 import NIFTY_50_SYMBOLS, NIFTY_50_MAP
from services.dashboard_service import DashboardService
from utils.health import check_backend_health

# Backend configuration
BACKEND_URL = "http://localhost:8000"

# ── Pro Tips (shown during Engine Loader) ─────────────────────
TIPS = [
    "We always show a **Stop Loss**. Never invest without one.",
    "Confidence above **75%** means the AI is very sure about its signal.",
    "The **Bear Case** tells you what could go wrong — always read it.",
    "Use **Today's Picks** for automated, beginner-friendly stock recommendations.",
    "MarketSense tracks **40+ technical indicators** so you don't have to.",
    "We monitor **Index Moods** and **India VIX** for macro-aware signals.",
    "Train custom AI models for any NIFTY 50 stock in **Model Management**.",
]

def health_check_ui():
    """Engine Initialization Loader — branding card with custom style."""
    placeholder = st.empty()
    tip = random.choice(TIPS)

    with placeholder.container():
        st.markdown(f"""
        <style>
        .loader-overlay {{
            display: flex; align-items: center; justify-content: center;
            min-height: 80vh; padding: 2rem;
        }}
        .loader-card {{
            background: #ffffff; border-radius: 1.25rem;
            box-shadow: 0 20px 60px -15px rgba(0, 0, 0, 0.12);
            border: 1px solid #e2e8f0; max-width: 460px; width: 100%;
            overflow: hidden;
        }}
        .loader-card-header {{
            padding: 2rem 2rem 1.25rem 2rem; text-align: center;
            border-bottom: 1px solid #f1f5f9;
        }}
        .loader-brand {{
            display: flex; align-items: center; justify-content: center; gap: 0.5rem;
        }}
        .loader-brand-icon {{ font-size: 2.2rem; }}
        .loader-brand-text {{
            font-size: 1.6rem; font-weight: 800; color: #000000;
        }}
        .loader-card-body {{
            padding: 2rem; display: flex; align-items: center;
            justify-content: center; gap: 1rem;
        }}
        .circular-spinner {{
            width: 28px; height: 28px; border: 3px solid #e2e8f0;
            border-top: 3px solid #2563eb; border-radius: 50%;
            animation: spin 0.8s linear infinite; flex-shrink: 0;
        }}
        @keyframes spin {{
            0%   {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        .loader-status {{
            font-size: 1.05rem; color: #64748b; font-weight: 500;
        }}
        .loader-card-footer {{
            padding: 1.25rem 2rem; background: #f8fafc;
            border-top: 1px solid #f1f5f9;
        }}
        .tip-label {{
            color: #2563eb; font-weight: 700; font-size: 0.75rem;
            letter-spacing: 0.06rem; text-transform: uppercase;
            margin-bottom: 0.3rem;
        }}
        .tip-text {{ color: #475569; font-size: 0.9rem; line-height: 1.45; }}
        </style>

        <div class="loader-overlay">
            <div class="loader-card">
                <div class="loader-card-header">
                    <div class="loader-brand">
                        <span class="loader-brand-icon">🚀</span>
                        <span class="loader-brand-text">MarketSense</span>
                    </div>
                </div>
                <div class="loader-card-body">
                    <div class="circular-spinner"></div>
                    <span class="loader-status">Loading...</span>
                </div>
                <div class="loader-card-footer">
                    <div class="tip-label">💡 Pro Tip</div>
                    <div class="tip-text">{tip}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Real health check runs while the card is displayed
        healthy, health_data = check_backend_health()
        time.sleep(2.0)

    placeholder.empty()
    return healthy, health_data

# ── Page Config (must be the very first st.* call) ───────────
st.set_page_config(
    page_title="MarketSense — AI Stock Predictor",
    page_icon="📈",
    layout="wide",
)

# Health check on startup
if "health_check_done" not in st.session_state:
    healthy, health_data = health_check_ui()
    st.session_state["backend_healthy"] = healthy
    st.session_state["health_data"] = health_data
    st.session_state["health_check_done"] = True

# ── Graceful Degradation (Native Streamlit Warning) ──
if not st.session_state.get("backend_healthy", False):
    st.warning("**Offline Mode:** Backend engine is unreachable. Some features (Predictions, Data Pipeline) are limited.")
    if st.button("🔄 Retry Connection", type="secondary"):
        st.session_state.pop("health_check_done", None)
        st.session_state.pop("backend_healthy", None)
        st.session_state.pop("health_data", None)
        st.rerun()

# ── Hero ──────────────────────────────────────────────────────
st.title("🚀 MarketSense")
st.subheader("AI-powered stock predictions for the Indian market. Clear signals, plain-English explanations — no jargon.")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image(
        "https://cdn.dribbble.com/users/1162077/screenshots/3848914/programmer.gif",
        width=500,
    )

st.write("")

# ── Feature Cards (Using native st.container with border) ──────
st.subheader("✨ Why MarketSense?")
st.write(
    "AI-powered analysis of Indian stocks — from technical indicators to "
    "news sentiment — all distilled into clear BUY / HOLD / AVOID signals."
)

c1, c2, c3 = st.columns(3)

with c1:
    with st.container(border=True):
        st.subheader("🤖 XGBoost Predictions")
        st.write("ML-powered direction predictions (BUY / HOLD / AVOID) with confidence scores and risk assessment.")

with c2:
    with st.container(border=True):
        st.subheader("📊 40+ Technical Indicators")
        st.write("RSI, MACD, Bollinger Bands, EMAs, ADX, ATR, OBV — automatically computed and stored.")

with c3:
    with st.container(border=True):
        st.subheader("💬 Plain-English Explanations")
        st.write("No jargon. Get key drivers like 'RSI shows oversold recovery' and bear-case risk warnings.")

st.write("")

# ── Quick Prediction ──────────────────────────────────────────
st.divider()
st.subheader("⚡ Quick Prediction")
st.write("Pick a NIFTY 50 stock and get an instant AI signal.")

qcol1, qcol2 = st.columns([2, 1])

with qcol1:
    quick_options = [f"{NIFTY_50_MAP[s]} ({s})" for s in NIFTY_50_SYMBOLS[:10]]
    quick_selected = st.selectbox("Stock", quick_options, index=0, key="quick_ticker")
    quick_symbol = quick_selected.split(" (")[-1].rstrip(")")

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
        
        with st.container(border=True):
            st.write(f"### {signals.get(direction, '🟡')} {direction}")
            st.write(f"**Stock:** {NIFTY_50_MAP.get(quick_symbol, quick_symbol)}")
            st.write(f"**AI Confidence:** {confidence:.0%}")
            st.write(f"**Horizon:** {result.get('horizon', 'short_term')}")

            drivers = result.get("key_drivers", [])
            if drivers:
                st.write("**Key Drivers:**")
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
    - 🌍 **Macro Awareness** — USD/INR, Crude, VIX, and Index Moods
    - 💬 **Beginner-Friendly** — Plain-English explanations, no jargon
    """)

with c2:
    st.image(
        "./assets/BrandLogoMarketSense.png",
        caption="Be fearful when others are greedy and greedy only when others are fearful.",
        width=200,
    )

st.write("")
st.divider()

# ── CTA ───────────────────────────────────────────────────────
st.write("### 💡 Ready to explore AI-powered investing?")
st.write("Navigate to the **Dashboard** from the sidebar to start analyzing stocks.")
st.caption(f"© {datetime.now().year} MarketSense | Built with ❤️ using FastAPI & Streamlit")
