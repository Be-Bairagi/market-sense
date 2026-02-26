import datetime

import pandas as pd
import streamlit as st

# --------------------------------
# Page Config
# --------------------------------
st.set_page_config(page_title="Settings - MarketSense", page_icon="⚙️", layout="wide")

st.title("⚙️ Settings & Management")
st.markdown(
    "#### Configure your MarketSense environment and manage models efficiently."
)

# --------------------------------
# Tabs
# --------------------------------
tab2, tab3, tab4 = st.tabs(["🌐 Data Source", "🎨 App Preferences", "💡 About System"])


# --------------------------------
# TAB 2: Data Source Settings
# --------------------------------
with tab2:
    st.subheader("🌐 Data Source Configuration")
    st.markdown("Choose the default data provider and API source for stock data.")

    source = st.selectbox(
        "Data Provider",
        ["Yahoo Finance (default)", "Alpha Vantage (API)", "Custom CSV Upload"],
        index=0,
    )
    if source == "Alpha Vantage (API)":
        st.text_input("Enter Alpha Vantage API Key:", type="password")
    elif source == "Custom CSV Upload":
        uploaded_file = st.file_uploader(
            "Upload your stock data CSV file", type=["csv"]
        )
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            st.write("✅ File uploaded successfully!")
            st.dataframe(df.head())
    st.info("Data provider preference saved locally (for demonstration).")

# --------------------------------
# TAB 3: App Preferences
# --------------------------------
with tab3:
    st.subheader("🎨 App Preferences")
    st.markdown("Customize how MarketSense behaves and looks.")

    default_ticker = st.text_input("Default Stock Ticker", "AAPL")
    theme_choice = st.selectbox("App Theme", ["Light", "Dark"], index=0)
    auto_refresh = st.checkbox("Enable Auto Refresh (every 5 minutes)", value=False)

    st.success(
        f"Preferences saved! (Default Ticker: {default_ticker}, Theme: {theme_choice})"
    )

# --------------------------------
# TAB 4: About System
# --------------------------------
with tab4:
    st.subheader("💡 System Information")
    st.write(f"""
    - **App Name:** MarketSense
    - **Version:** 1.0.0
    - **Last Updated:** {datetime.date.today().strftime('%Y-%m-%d')}
    - **Developer:** Brotati Bairagi
    - **Backend:** FastAPI
    - **Frontend:** Streamlit
    - **Data Source:** Yahoo Finance (default)
    - **Model Type:** Prophet (default)
    """)

    st.markdown("---")
    st.info(
        "Future versions will include user authentication, advanced model registry, and multi-API data pipelines."  # noqa: E501
    )  # noqa: E501
