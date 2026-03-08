import logging

import pandas as pd
import streamlit as st
from data.nifty50 import NIFTY_50_SYMBOLS, NIFTY_50_MAP
from services.dashboard_service import DashboardService

logger = logging.getLogger(__name__)

# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Data Pipeline | MarketSense",
    page_icon="🗄️",
    layout="wide",
)

st.title("🗄️ Data & Feature Pipeline")
st.write("Monitor data coverage, macro indicators, and feature store status.")

st.markdown("---")

# ── Section 1: Data Coverage ─────────────────────────────────
st.subheader("📦 Data Coverage")

col1, col2 = st.columns([2, 1])

with col1:
    if st.button("🔄 Refresh Data Status", use_container_width=True):
        st.session_state["data_status_loaded"] = True

if st.session_state.get("data_status_loaded"):
    with st.spinner("Fetching data status..."):
        data_status = DashboardService.fetch_data_status()

    if data_status.get("error"):
        st.error(f"❌ {data_status['error']}")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("📊 Stocks with Price Data", data_status.get("unique_stocks_cached", 0))
        c2.metric("📡 System Status", data_status.get("system_status", "Unknown"))
        latest = data_status.get("latest_macro_sync", [])
        c3.metric("🌍 Macro Indicators", len(latest) if latest else 0)

st.markdown("---")

# ── Section 2: Macro Indicators ──────────────────────────────
st.subheader("🌍 Macro Indicators")

if st.button("📊 Load Macro Data", use_container_width=True):
    with st.spinner("Fetching macro indicators..."):
        macro = DashboardService.fetch_macro_data()

    if isinstance(macro, list) and macro:
        rows = []
        for item in macro:
            rows.append({
                "Indicator": item.get("indicator", "N/A"),
                "Value": item.get("value", "N/A"),
                "Date": item.get("date", "N/A"),
            })
        df_macro = pd.DataFrame(rows)
        st.dataframe(df_macro, use_container_width=True, hide_index=True)
    elif isinstance(macro, dict) and macro.get("error"):
        st.error(f"❌ {macro['error']}")
    else:
        st.info("No macro data available. Run a macro data update from the backend.")

st.markdown("---")

# ── Section 3: Feature Store ─────────────────────────────────
st.subheader("🧬 Feature Store")

if st.button("🔄 Refresh Feature Status", use_container_width=True):
    st.session_state["feature_status_loaded"] = True

if st.session_state.get("feature_status_loaded"):
    with st.spinner("Fetching feature store status..."):
        feat_status = DashboardService.fetch_feature_status()

    if feat_status.get("error"):
        st.error(f"❌ {feat_status['error']}")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("📐 Total Feature Vectors", feat_status.get("total_feature_vectors", 0))
        c2.metric("📈 Symbols Covered", feat_status.get("unique_symbols", 0))
        c3.metric("🟢 Status", feat_status.get("system_status", "Unknown"))

        symbols = feat_status.get("symbols", [])
        if symbols:
            st.markdown("**Covered symbols:** " + ", ".join(f"`{s}`" for s in symbols))

st.markdown("---")

# ── Section 4: Backfill Controls ─────────────────────────────
st.subheader("⚡ Backfill Controls")
st.caption("Trigger data or feature backfills for any NIFTY 50 stock.")

ticker_options = [f"{s} — {NIFTY_50_MAP[s]}" for s in NIFTY_50_SYMBOLS]
selected = st.selectbox("Select Stock", ticker_options, index=0, key="backfill_ticker")
backfill_symbol = selected.split(" — ")[0]

col_a, col_b = st.columns(2)

with col_a:
    if st.button("📥 Backfill Price Data", use_container_width=True):
        with st.spinner(f"Starting price backfill for {backfill_symbol}..."):
            res = DashboardService.backfill_data(backfill_symbol)
        if res.get("error"):
            st.error(f"❌ {res['error']}")
        else:
            st.success(f"✅ {res.get('message', 'Started!')}")
            st.info("⏳ Runs in background. Check logs for progress.")

with col_b:
    if st.button("🧬 Backfill Features", use_container_width=True):
        with st.spinner(f"Starting feature backfill for {backfill_symbol}..."):
            res = DashboardService.backfill_features(backfill_symbol)
        if res.get("error"):
            st.error(f"❌ {res['error']}")
        else:
            st.success(f"✅ {res.get('message', 'Started!')}")
            st.info("⏳ Runs in background (~5 min). Check logs for progress.")

st.markdown("---")

# ── Section 5: Feature Explorer ──────────────────────────────
st.subheader("🔬 Feature Explorer")
st.caption("View the latest computed feature vector for a symbol.")

explorer_options = [f"{s} — {NIFTY_50_MAP[s]}" for s in NIFTY_50_SYMBOLS]
explorer_selected = st.selectbox("Select Stock", explorer_options, index=0, key="explorer_ticker")
explorer_symbol = explorer_selected.split(" — ")[0]

if st.button("🔍 View Latest Features", use_container_width=True):
    with st.spinner(f"Fetching features for {explorer_symbol}..."):
        fv = DashboardService.fetch_feature_vector(explorer_symbol)

    if fv.get("error"):
        st.warning(f"No features available: {fv['error']}")
    else:
        st.success(f"📅 Date: {fv.get('date', 'N/A')} | Horizon: {fv.get('horizon', 'N/A')}")

        features = fv.get("features", {})
        if features:
            # Group features by type
            tech = {k: v for k, v in features.items() if not any(
                k.startswith(p) for p in ["sentiment", "usd", "brent", "india_vix", "nifty", "fii", "dii"]
            )}
            macro = {k: v for k, v in features.items() if any(
                k.startswith(p) for p in ["usd", "brent", "india_vix"]
            )}
            market = {k: v for k, v in features.items() if any(
                k.startswith(p) for p in ["nifty", "fii", "dii"]
            )}
            sent = {k: v for k, v in features.items() if k.startswith("sentiment")}

            tab1, tab2, tab3, tab4 = st.tabs(["📈 Technical", "🌍 Macro", "📊 Market", "💬 Sentiment"])

            with tab1:
                if tech:
                    df = pd.DataFrame(list(tech.items()), columns=["Feature", "Value"])
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No technical features.")

            with tab2:
                if macro:
                    df = pd.DataFrame(list(macro.items()), columns=["Feature", "Value"])
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No macro features.")

            with tab3:
                if market:
                    df = pd.DataFrame(list(market.items()), columns=["Feature", "Value"])
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No market context features.")

            with tab4:
                if sent:
                    df = pd.DataFrame(list(sent.items()), columns=["Feature", "Value"])
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No sentiment features.")
        else:
            st.info("Feature vector is empty.")
