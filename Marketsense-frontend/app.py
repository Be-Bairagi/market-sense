# app.py
import random
import time
from datetime import datetime
import streamlit as st
import requests
from data.nifty50 import NIFTY_50_SYMBOLS, NIFTY_50_MAP
from services.dashboard_service import DashboardService
from utils.health import check_backend_health

# Backend configuration
BACKEND_URL = "http://localhost:8000"
HEALTH_ENDPOINT = f"{BACKEND_URL}/health"

# ── Pro Tips (shown during Engine Loader) ─────────────────────
TIPS = [
    "We always show a <strong>Stop Loss</strong>. Never invest without one.",
    "Confidence above <strong>75%</strong> means the AI is very sure about its signal.",
    "The <strong>Bear Case</strong> tells you what could go wrong — always read it.",
    "Use <strong>Today's Picks</strong> for automated, beginner-friendly stock recommendations.",
    "MarketSense tracks <strong>40+ technical indicators</strong> so you don't have to.",
    "We monitor <strong>FII &amp; DII flows</strong> and <strong>India VIX</strong> for macro-aware signals.",
    "Train custom AI models for any NIFTY 50 stock in <strong>Model Management</strong>.",
]



def health_check_ui():
    """Engine Initialization Loader — centered card with branding, spinner, and tips."""
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
        /* ── Card Header ── */
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
        /* ── Card Body ── */
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
        /* ── Card Footer ── */
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
        # Hold the card visible for a moment so the user sees the branding
        time.sleep(2.5)

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

# ── Service Status Page (shown when backend is unreachable) ──
# ── Graceful Degradation (Soft Banner when backend is down) ──
if not st.session_state.get("backend_healthy", False):
    st.markdown("""
    <style>
    .degraded-banner {
        background: #fffbeb; border: 1px solid #fde68a;
        border-radius: 0.75rem; padding: 1rem 1.5rem;
        display: flex; align-items: center; justify-content: space-between;
        margin-bottom: 2rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .degraded-content { display: flex; align-items: center; gap: 0.75rem; }
    .degraded-icon { font-size: 1.25rem; }
    .degraded-text { color: #92400e; font-weight: 500; font-size: 0.95rem; }
    </style>
    <div class="degraded-banner">
        <div class="degraded-content">
            <span class="degraded-icon">⚠️</span>
            <span class="degraded-text">
                <strong>Offline Mode:</strong> Backend engine is unreachable. Some features (Predictions, Data Pipeline) are limited.
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Retry button in a small column to keep it neat
    col_retry, _ = st.columns([1, 4])
    with col_retry:
        if st.button("🔄 Retry Connection", type="secondary", use_container_width=True, key="retry_health_banner"):
            st.session_state.pop("health_check_done", None)
            st.session_state.pop("backend_healthy", None)
            st.session_state.pop("health_data", None)
            st.rerun()



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
        colors = {"BUY": "#16a34a", "HOLD": "#ca8a04", "AVOID": "#dc2626"}

        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #f8fafc, #e2e8f0);
            border-left: 5px solid {colors.get(direction, '#64748b')};
            border-radius: 0.75rem; padding: 1.5rem; margin: 1rem 0;
        ">
            <div style="font-size: 0.9rem; color: #64748b; margin-bottom: 0.5rem;">{NIFTY_50_MAP.get(quick_symbol, quick_symbol)}</div>
            <span style="font-size: 2.5rem;">{signals.get(direction, '🟡')}</span>
            <span style="font-size: 2rem; font-weight: 700; color: {colors.get(direction, '#64748b')}; margin-left: 0.5rem;">
                {direction}
            </span>
            <div style="color: #64748b; margin-top: 0.5rem;">
                Confidence: {confidence:.0%} · {result.get('horizon', 'short_term')}
            </div>
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
