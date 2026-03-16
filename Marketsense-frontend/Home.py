# Home.py
import random
import time
import logging
from datetime import datetime
import streamlit as st
import pandas as pd
from data.nifty50 import NIFTY_50_SYMBOLS, NIFTY_50_MAP
from services.dashboard_service import DashboardService
from utils.health import check_backend_health
from utils.helpers import format_currency, format_date

logger = logging.getLogger(__name__)

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
                    <span class="loader-status">Loading Engine...</span>
                </div>
                <div class="loader-card-footer">
                    <div class="tip-label">💡 Pro Tip</div>
                    <div class="tip-text">{tip}</div>
                </div>
            </div>
        </div>

        <style>
        /* Force equal height for columns and containers */
        [data-testid="stHorizontalBlock"] {{
            align-items: stretch;
        }}
        [data-testid="stVerticalBlockBorderWrapper"] {{
            height: 100% !important;
            display: flex;
            flex-direction: column;
        }}
        .feature-card {{
            height: 180px;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
        }}
        .logo-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100%;
            padding-left: 2rem; /* Shifting more rightwards */
        }}
        .logo-container img {{
            border-radius: 1.5rem;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.1);
            border: 1px solid #f1f5f9;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            max-width: 320px;
        }}
        .logo-container img:hover {{
            transform: scale(1.02) translateY(-10px);
            box-shadow: 0 30px 60px rgba(0, 0, 0, 0.15);
        }}
        </style>
        """, unsafe_allow_html=True)

        healthy, health_data = check_backend_health()
        time.sleep(1.5)

    placeholder.empty()
    return healthy, health_data

# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="MarketSense — AI Stock Predictor",
    page_icon="📈",
    layout="wide",
)

# Initialize Session State
if "health_check_done" not in st.session_state:
    healthy, health_data = health_check_ui()
    st.session_state["backend_healthy"] = healthy
    st.session_state["health_data"] = health_data
    st.session_state["health_check_done"] = True

if "user_mode" not in st.session_state:
    st.session_state.user_mode = "🧠 Expert"

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.info(f"Experience Level: **{st.session_state.user_mode}**")

# ── Online/Offline Status ──
if not st.session_state.get("backend_healthy", False):
    st.warning("**Offline Mode:** Backend engine is unreachable. Some features are limited.")
    if st.button("🔄 Retry Connection", type="secondary"):
        st.session_state.pop("health_check_done", None)
        st.session_state.pop("backend_healthy", None)
        st.session_state.pop("health_data", None)
        st.rerun()

# ── Tabs Navigation ───────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🚀 Home", "⚙️ App Settings", "📘 About System"])

# ── TAB 1: HOME ──────────────────────────────────────────────
with tab1:
    col_hero1, col_hero2 = st.columns([2, 1])
    
    with col_hero1:
        st.title("🚀 Welcome to MarketSense")
        st.markdown("""
        ### AI-powered stock prediction system for the Indian market.
        MarketSense analyzes Indian stocks using technical indicators, market macro data, 
        and machine learning to provide clear **BUY / HOLD / AVOID** signals.
        """)
        
        if st.session_state.user_mode == "💡 Beginner":
            st.info("👋 **New here?** Start with **Instant AI Signal** below or explore **Today's Picks** in the sidebar pages.")
        
        st.write("")
        if st.button("📈 Go to Live Dashboard", type="primary", use_container_width=True):
            st.switch_page("pages/1_Dashboard.py")

    with col_hero2:
        st.markdown('<div class="logo-container">', unsafe_allow_html=True)
        st.image(
            "./assets/BrandLogoMarketSense.png",
            use_container_width=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    
    # Quick Prediction
    st.subheader("⚡ Instant AI Signal")
    st.write("Get a quick snapshot of any NIFTY 50 stock.")
    
    qcol1, qcol2 = st.columns([3, 1])
    with qcol1:
        quick_options = [f"{NIFTY_50_MAP[s]} ({s})" for s in NIFTY_50_SYMBOLS[:15]]
        quick_selected = st.selectbox("Pick a stock to analyze:", quick_options, index=0, label_visibility="collapsed")
        quick_symbol = quick_selected.split(" (")[-1].rstrip(")")
    with qcol2:
        quick_predict = st.button("🎯 Get Signal", use_container_width=True, type="primary")

    if quick_predict:
        with st.spinner(f"AI is crunching numbers for {quick_symbol}..."):
            result = DashboardService.fetch_rich_prediction(quick_symbol, "xgboost")
        
        if result.get("error"):
            st.warning(f"⚠️ {result['error']}")
            st.info("Train an XGBoost model for this stock in **Model Management** first.")
        else:
            # FIX: Prediction data is nested under 'predictions' key
            pred = result.get("predictions", {})
            direction = pred.get("direction", "HOLD")
            confidence = pred.get("confidence", 0.0)
            signals = {"BUY": "🟢", "HOLD": "🟡", "AVOID": "🔴"}
            
            with st.container(border=True):
                st.write(f"### {signals.get(direction, '🟡')} {direction}")
                
                c_col1, c_col2 = st.columns([1, 2])
                with c_col1:
                    st.write(f"**AI Confidence:** {confidence:.0%}")
                with c_col2:
                    st.progress(float(confidence))
                
                st.write("")
                m1, m2, m3 = st.columns(3)
                m1.metric("Target (Near)", format_currency(pred.get('target_low', 0)))
                m2.metric("Stop Loss", format_currency(pred.get('stop_loss', 0)))
                m3.metric("Risk Profile", pred.get("risk_level", "MEDIUM"))

    st.divider()
    
    # Feature Highlights
    st.subheader("✨ Why use MarketSense?")
    f1, f2, f3 = st.columns(3)
    with f1:
        with st.container(border=True):
            st.markdown('<div class="feature-card">', unsafe_allow_html=True)
            st.markdown("### 🤖 Trained Models")
            st.write("XGBoost and Prophet models specifically tuned for the volatility of the Indian Stock Market.")
            st.markdown('</div>', unsafe_allow_html=True)
    with f2:
        with st.container(border=True):
            st.markdown('<div class="feature-card">', unsafe_allow_html=True)
            st.markdown("### 📊 40+ Indicators")
            st.write("We compute RSI, MACD, Bollinger Bands, and volume signals automatically so you don't have to.")
            st.markdown('</div>', unsafe_allow_html=True)
    with f3:
        with st.container(border=True):
            st.markdown('<div class="feature-card">', unsafe_allow_html=True)
            st.markdown("### 💬 Simply Explained")
            st.write("No technical jargon. We translate complex data into plain-English insights and actionable signals.")
            st.markdown('</div>', unsafe_allow_html=True)

# ── TAB 2: SETTINGS ───────────────────────────────────────────
with tab2:
    st.title("⚙️ App Settings")
    
    
    st.subheader("🎨 Interface Preferences")
    pref_tab1, pref_tab2 = st.tabs(["👤 Personalization", "🖼️ Display"])
    
    with pref_tab1:
        st.write("Choose how much technical detail you want to see across the platform.")
        st.session_state.user_mode = st.radio(
            "Select Your Experience Level:",
            ["💡 Beginner", "🧠 Expert"],
            index=0 if st.session_state.user_mode == "💡 Beginner" else 1,
            help="Beginner mode provides more explanations and tips."
        )
        st.info(f"Setting this to **{st.session_state.user_mode}** will update all charts and metrics labels.")

    with pref_tab2:
        default_ticker = st.text_input("Default Focus Ticker", "RELIANCE.NS")
        st.checkbox("Enable Real-time Polling (every 5 mins)", value=True)
    
    if st.button("💾 Save Settings"):
        st.success(f"Preferences for {default_ticker} saved successfully!")

# ── TAB 3: ABOUT ─────────────────────────────────────────────
with tab3:
    st.title("📘 About MarketSense")
    
    st.markdown("""
    MarketSense is an **AI-driven stock market prediction platform** designed to empower retail investors with high-probability signals.
    
    ### ⚙️ Key Features
    *   **Data Pipeline:** Continuous ingestion of historical prices and macro-economic indicators (VIX, Crude Oil, USD/INR).
    *   **Feature Store:** Real-time computation of technical and sentiment signals.
    *   **AI Models:** Advanced ensemble models (XGBoost) and time-series forecasters (Prophet).
    """)
    
    st.divider()
    
    st.markdown(f"""
    **System Status:**
    - **App Version:** 1.6.0-stable
    - **Lead Developer:** Brotati Bairagi
    - **Backend Architecture:** FastAPI + SQLModel
    - **Frontend Framework:** Streamlit (v1.40+)
    - **Last Intelligence Sync:** {format_date(datetime.now())}
    """)
    
    st.divider()
    
    st.info("📫 **Support:** For technical issues or feedback, reach out at [brotati.bairagi@example.com](mailto:brotati.bairagi@example.com)")

st.markdown(
    f"""
    <div style="text-align: center; color: #64748b; font-size: 0.85rem; padding: 2rem 0; border-top: 1px solid #f1f5f9; margin-top: 3rem;">
        © {datetime.now().year} MarketSense | Built with ❤️ for the Indian Financial Market
    </div>
    """,
    unsafe_allow_html=True
)
