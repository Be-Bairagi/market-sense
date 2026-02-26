# components/metrics.py
import streamlit as st


def show_metrics(mae, rmse, r2):
    c1, c2, c3 = st.columns(3)
    c1.metric("Mean Absolute Error (MAE)", f"{mae:.2f}")
    c2.metric("Root Mean Square Error (RMSE)", f"{rmse:.2f}")
    c3.metric("R² Score", f"{r2:.2f}")
