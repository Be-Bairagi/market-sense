# app.py
import random
import time
from datetime import datetime
import streamlit as st
import pandas as pd
from data.nifty50 import NIFTY_50_SYMBOLS, NIFTY_50_MAP
from services.dashboard_service import DashboardService
from utils.health import check_backend_health
from utils.helpers import format_currency, format_date

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

        healthy, health_data = check_backend_health()
        time.sleep(2.0)

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
    st.session_state.user_mode = "💡 Beginner"

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.header("👤 Personalization")
    st.session_state.user_mode = st.radio(
        "Select Your Experience Level:",
        ["💡 Beginner", "🧠 Expert"],
        index=0 if st.session_state.user_mode == "💡 Beginner" else 1,
        help="Beginner mode provides more explanations and tips."
    )
    st.divider()
    st.info(f"Currently in **{st.session_state.user_mode}** mode.")

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
    st.title("🚀 Welcome to MarketSense")
    st.subheader("AI-powered stock predictions for the Indian market.")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write(
            "MarketSense analyzes Indian stocks using technical indicators, market macro data, "
            "and machine learning to provide clear BUY / HOLD / AVOID signals."
        )
        st.write("")
        if st.session_state.user_mode == "💡 Beginner":
            st.info("👋 New here? Start with **Quick Prediction** below or check out the **Today's Picks** in the sidebar pages.")
    
    with col2:
        st.image(
            "./assets/BrandLogoMarketSense.png",
            width=200,
        )

    st.divider()
    
    # Quick Prediction
    st.subheader("⚡ Instant AI Signal")
    qcol1, qcol2 = st.columns([2, 1])
    with qcol1:
        quick_options = [f"{NIFTY_50_MAP[s]} ({s})" for s in NIFTY_50_SYMBOLS[:15]]
        quick_selected = st.selectbox("Pick a stock to analyze:", quick_options, index=0)
        quick_symbol = quick_selected.split(" (")[-1].rstrip(")")
    with qcol2:
        st.write("") # Spacer
        quick_predict = st.button("🎯 Get Signal", use_container_width=True, type="primary")

    if quick_predict:
        with st.spinner(f"AI is crunching numbers for {quick_symbol}..."):
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
                st.write(f"**Confidence:** {confidence:.0%}")
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Target (Near)", format_currency(result.get('target_low', 0)))
                m2.metric("Stop Loss", format_currency(result.get('stop_loss', 0)))
                m3.metric("Risk Level", result.get("risk_level", "MEDIUM"))

    st.divider()
    
    # Feature Highlights
    st.subheader("✨ Key Features")
    f1, f2, f3 = st.columns(3)
    with f1:
        with st.container(border=True):
            st.markdown("### 🤖 ML Models")
            st.write("XGBoost direction classifiers and Prophet price forecasters tuned for Indian stocks.")
    with f2:
        with st.container(border=True):
            st.markdown("### 📊 40+ Indicators")
            st.write("Automatically calculated RSI, MACD, Bollinger Bands, and more stored in the feature store.")
    with f3:
        with st.container(border=True):
            st.markdown("### 💬 Plain English")
            st.write("No complex jargon. We translate technical signals into simple bullet points.")

# ── TAB 2: SETTINGS ───────────────────────────────────────────
with tab2:
    st.title("⚙️ App Settings")
    
    st.subheader("🌐 Data Source Configuration")
    source = st.selectbox(
        "Primary Data Provider",
        ["Yahoo Finance (Internal)", "Alpha Vantage (Upcoming)", "Custom Upload (Dev Only)"],
        index=0
    )
    if source == "Custom Upload (Dev Only)":
        st.file_uploader("Upload CSV", type=["csv"])
    
    st.divider()
    
    st.subheader("🎨 Interface Preferences")
    default_ticker = st.text_input("Default Focus Ticker", "RELIANCE.NS")
    st.checkbox("Enable Auto-Refresh (Market Hours Only)", value=True)
    
    if st.button("💾 Save Preferences"):
        st.success("Preferences saved successfully!")

# ── TAB 3: ABOUT ─────────────────────────────────────────────
with tab3:
    st.title("📘 About MarketSense")
    
    st.markdown("""
    MarketSense is developed as an **AI-driven stock market prediction platform** to assist retail investors 
    in identifying high-probability opportunities in the **NIFTY 50** universe.
    
    ### ⚙️ How it Works
    1. **Data Pipeline:** Fetches historical and macro data (VIX, Crude, FII/DII).
    2. **Feature Store:** Computes technical and sentiment signals automatically.
    3. **AI Models:** Multiple frameworks (Prophet, XGBoost) analyze data for patterns.
    4. **Screener:** Nightly scans identify the top 5 'High Confidence' picks.
    """)
    
    st.divider()
    
    st.markdown(f"""
    **System Information:**
    - **App Version:** 1.5.0-master
    - **Developer:** Brotati Bairagi
    - **Backend:** FastAPI (Python)
    - **Frontend:** Streamlit
    - **Last System Sync:** {format_date(datetime.now())}
    """)
    
    st.divider()
    
    st.write("📫 **Contact & Support:** [brotati.bairagi@example.com](mailto:brotati.bairagi@example.com)")

st.caption(f"© {datetime.now().year} MarketSense | Built with ❤️ using FastAPI + Streamlit")
