# components/charts.py
import plotly.express as px
import streamlit as st


def plot_predictions(df, ticker):
    fig = px.line(
        df,
        x="date",
        y=["actual", "predicted"],
        title=f"{ticker} - Predicted vs Actual Prices",
        labels={"value": "Price", "date": "Date"},
    )
    st.plotly_chart(fig, width="stretch")


def plot_model_comparison(df):
    fig = px.bar(
        df,
        x="model",
        y=["MAE", "RMSE"],
        barmode="group",
        title="Model Performance Comparison",
    )
    st.plotly_chart(fig, width="stretch")
