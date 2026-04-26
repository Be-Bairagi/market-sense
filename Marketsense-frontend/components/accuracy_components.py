import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go
import plotly.express as px
from utils.helpers import format_currency, format_date, CURRENCY_SYMBOL

def render_health_chips(metrics: dict):
    """Render 3 model health status chips."""
    today = datetime.date.today()

    # 1. Retrain age
    trained_on = metrics.get("trained_on")
    if trained_on and trained_on != "Unknown":
        try:
            trained_date = datetime.datetime.strptime(trained_on[:10], "%Y-%m-%d").date()
            age_days = (today - trained_date).days
            if age_days <= 7:
                retrain_color, retrain_icon = "#22c55e", "🟢"
            elif age_days <= 30:
                retrain_color, retrain_icon = "#f59e0b", "🟡"
            else:
                retrain_color, retrain_icon = "#ef4444", "🔴"
            retrain_label = f"{retrain_icon} Retrained {age_days}d ago"
        except:
            retrain_color, retrain_label = "#94a3b8", "⚪ Date error"
    else:
        retrain_color, retrain_label = "#94a3b8", "⚪ Retrain date unknown"

    # 2. Data freshness
    end_date = metrics.get("training_metrics", {}).get("end_date")
    if end_date:
        try:
            end_d = datetime.datetime.strptime(end_date[:10], "%Y-%m-%d").date()
            data_age = (today - end_d).days
            if data_age <= 7:
                data_color, data_icon = "#22c55e", "🟢"
            elif data_age <= 30:
                data_color, data_icon = "#f59e0b", "🟡"
            else:
                data_color, data_icon = "#ef4444", "🔴"
            data_label = f"{data_icon} Data: {data_age}d old"
        except:
            data_color, data_label = "#94a3b8", "⚪ Date error"
    else:
        data_color, data_label = "#94a3b8", "⚪ Data date unknown"

    # 3. Eval status
    eval_status = metrics.get("eval_status", "live")
    if eval_status == "live":
        eval_color, eval_label = "#22c55e", "🟢 Live Evaluation"
    else:
        eval_color, eval_label = "#f59e0b", "🟡 Stored Metrics Only"

    c1, c2, c3 = st.columns(3)
    chip_style = (
        'style="background:{bg}; color:#fff; padding:0.4rem 1rem; '
        'border-radius:999px; font-weight:600; font-size:0.85rem; '
        'display:inline-block; border: 1px solid rgba(255,255,255,0.1);"'
    )
    c1.markdown(f'<span {chip_style.format(bg=retrain_color)}>{retrain_label}</span>', unsafe_allow_html=True)
    c2.markdown(f'<span {chip_style.format(bg=data_color)}>{data_label}</span>', unsafe_allow_html=True)
    c3.markdown(f'<span {chip_style.format(bg=eval_color)}>{eval_label}</span>', unsafe_allow_html=True)

def render_hero_accuracy(metrics: dict, is_beginner: bool):
    """Render the hero accuracy card."""
    acc_pct = metrics.get("accuracy_pct", 0.0)
    data_pts = metrics.get("data_points", 0)
    model_cat = metrics.get("model_category", "classification")

    if acc_pct >= 70:
        color, verdict = "#22c55e", "Strong"
    elif acc_pct >= 55:
        color, verdict = "#f59e0b", "Moderate"
    else:
        color, verdict = "#ef4444", "Needs Improvement"

    with st.container(border=True):
        st.markdown(
            f'<div style="text-align:center; padding:1.5rem 0;">'
            f'<p style="font-size:1.1rem; color:#64748b; margin:0; font-weight:500;">🎯 Model Accuracy</p>'
            f'<p style="font-size:4.5rem; font-weight:900; color:{color}; margin:1rem 0; line-height:1;">'
            f'{acc_pct:.1f}%</p>'
            f'<p style="font-size:1.1rem; color:#64748b; margin:0;">'
            f'Confidence Verdict: <strong style="color:{color}">{verdict}</strong></p>'
            f'</div>',
            unsafe_allow_html=True
        )
        st.progress(min(float(acc_pct) / 100, 1.0))

        if is_beginner:
            if model_cat == "classification":
                st.caption(
                    f"This model correctly predicted the trend (BUY/HOLD/AVOID) "
                    f"**{acc_pct:.1f}%** of the time, based on **{data_pts}** historical samples."
                )
            else:
                st.caption(
                    f"This model predicted the correct price direction "
                    f"**{acc_pct:.1f}%** of the time, based on **{data_pts}** historical price points."
                )
        else:
            metric_desc = 'accuracy_score' if model_cat == 'classification' else 'directional prediction sign match'
            st.caption(f"Evaluated on {data_pts} samples using {metric_desc}.")

def render_kpi_cards(metrics: dict, model_category: str, is_beginner: bool):
    """Render metrics tiles based on model category."""
    
    if model_category == "regression":
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        kpi1.metric(
            "Avg. Price Error" if is_beginner else "MAE",
            format_currency(metrics.get("MAE", 0)),
            help="Mean Absolute Error — average gap between predicted and actual price in ₹"
        )
        kpi2.metric(
            "Precision Score" if is_beginner else "RMSE",
            format_currency(metrics.get("RMSE", 0)),
            help="Root Mean Squared Error — penalizes large mistakes more heavily"
        )
        r2_val = metrics.get("R2")
        kpi3.metric(
            "Reliability Score" if is_beginner else "R² Score",
            f"{r2_val:.3f}" if r2_val is not None else "⚠️ N/A",
            help="R² (0 to 1) — how much of the price movement the model explains. Higher = better."
        )
        mape_val = metrics.get("MAPE")
        kpi4.metric(
            "Error %" if is_beginner else "MAPE",
            f"{mape_val:.2f}%" if mape_val is not None else "⚠️ N/A",
            help="Mean Absolute Percentage Error — percentage error, comparable across stocks"
        )
        dir_acc = metrics.get("directional_accuracy", 0)
        kpi5.metric(
            "Trend Accuracy" if is_beginner else "Dir. Accuracy",
            f"{dir_acc:.1%}",
            help="How often the model got the UP/DOWN direction correct"
        )
    else:
        # Classification
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        acc = metrics.get("accuracy_pct", 0) / 100
        dir_acc = metrics.get("directional_accuracy", acc)
        
        kpi1.metric(
            "Overall Accuracy" if is_beginner else "Accuracy",
            f"{acc:.1%}",
            help="Percentage of all predictions (BUY/HOLD/AVOID) that were correct"
        )
        kpi2.metric(
            "Trend Accuracy" if is_beginner else "Dir. Accuracy",
            f"{dir_acc:.1%}",
            help="Accuracy on BUY/AVOID decisions only (ignoring HOLD)"
        )

        precision = metrics.get("precision_per_class", {})
        recall = metrics.get("recall_per_class", {})
        f1 = metrics.get("f1_per_class", {})

        buy_prec = precision.get("BUY", 0) if precision else 0
        buy_recall = recall.get("BUY", 0) if recall else 0
        buy_f1 = f1.get("BUY", 0) if f1 else 0

        kpi3.metric(
            "Signal Reliability" if is_beginner else "Precision (BUY)",
            f"{buy_prec:.1%}" if precision else "⚠️ N/A",
            help="When the AI says BUY, how often is it actually correct?"
        )
        kpi4.metric(
            "Signal Coverage" if is_beginner else "Recall (BUY)",
            f"{buy_recall:.1%}" if recall else "⚠️ N/A",
            help="Of all the real BUY opportunities, how many did the AI catch?"
        )
        kpi5.metric(
            "Balance Score" if is_beginner else "F1 (BUY)",
            f"{buy_f1:.1%}" if f1 else "⚠️ N/A",
            help="F1 balances Signal Reliability and Coverage into one number"
        )

def render_confusion_matrix(metrics: dict, is_beginner: bool):
    """Render a Plotly heatmap confusion matrix."""
    cm_data = metrics.get("confusion_matrix")
    if not cm_data:
        return

    st.subheader("🔢 Prediction Breakdown" if is_beginner else "🔢 Confusion Matrix")
    if is_beginner:
        st.caption("This table shows where the AI was right (diagonal) and where it got mixed up.")

    fig = go.Figure(data=go.Heatmap(
        z=cm_data["matrix"],
        x=cm_data["labels"],
        y=cm_data["labels"],
        colorscale="Blues",
        text=cm_data["matrix"],
        texttemplate="%{text}",
        hovertemplate="Predicted: %{x}<br>Actual: %{y}<br>Count: %{z}<extra></extra>"
    ))
    fig.update_layout(
        xaxis_title="AI Prediction",
        yaxis_title="Actual Outcome",
        yaxis=dict(autorange="reversed"),
        template="plotly_white",
        height=400,
        width=500,
        margin=dict(t=20, b=20, l=20, r=20)
    )
    st.plotly_chart(fig, use_container_width=False)

def render_residuals(df: pd.DataFrame, model_category: str, is_beginner: bool):
    """Render residuals histogram for regression models."""
    if model_category != "regression" or "predicted" not in df.columns:
        return

    st.subheader("📉 Error Distribution" if is_beginner else "📉 Residual Distribution")
    if is_beginner:
        st.caption("Shows how far off the AI's errors were. Tight bell-curves near 0 are better.")
    
    df["residual"] = df["actual"] - df["predicted"]
    fig_resid = px.histogram(df, x="residual", nbins=30,
                             labels={"residual": "Error (₹)"},
                             color_discrete_sequence=["#2563eb"])
    fig_resid.update_layout(template="plotly_white", height=400)
    st.plotly_chart(fig_resid, use_container_width=True)

def render_academic_summary(metrics: dict, period: str):
    """Render a clean copy-pasteable table for academic reports."""
    with st.expander("🎓 Academic Report (Copy for Professor)", expanded=False):
        st.markdown("### 📋 Model Evaluation Summary")
        col_m1, col_m2 = st.columns(2)
        col_m1.write(f"**Ticker:** {metrics.get('ticker')}")
        col_m1.write(f"**Model:** {metrics.get('model_type')}")
        col_m2.write(f"**Eval Period:** {period}")
        col_m2.write(f"**Trained On:** {metrics.get('trained_on', 'N/A')}")
        st.divider()

        model_cat = metrics.get("model_category", "regression")
        if model_cat == "classification":
            summary = {
                "Metric": ["Accuracy", "Directional Accuracy", "Precision (BUY)", "Recall (BUY)", "F1 Score (BUY)", "Samples"],
                "Value": [
                    f"{metrics.get('accuracy_pct', 0):.2f}%",
                    f"{metrics.get('directional_accuracy', 0):.2%}",
                    f"{metrics.get('precision_per_class', {}).get('BUY', 0):.2%}" if metrics.get("precision_per_class") else "N/A",
                    f"{metrics.get('recall_per_class', {}).get('BUY', 0):.2%}" if metrics.get("recall_per_class") else "N/A",
                    f"{metrics.get('f1_per_class', {}).get('BUY', 0):.2%}" if metrics.get("f1_per_class") else "N/A",
                    metrics.get("data_points", "N/A")
                ]
            }
        else:
            summary = {
                "Metric": ["Directional Accuracy", "MAE", "RMSE", "R²", "MAPE", "Samples"],
                "Value": [
                    f"{metrics.get('accuracy_pct', 0):.2f}%",
                    f"{CURRENCY_SYMBOL}{metrics.get('MAE', 0):.2f}",
                    f"{CURRENCY_SYMBOL}{metrics.get('RMSE', 0):.2f}",
                    f"{metrics.get('R2', 0):.4f}",
                    f"{metrics.get('MAPE', 0):.2f}%",
                    metrics.get("data_points", "N/A")
                ]
            }
        
        st.table(pd.DataFrame(summary))

def render_training_metadata(metrics: dict):
    """Render detailed training stats."""
    with st.expander("🔧 Model Training Metadata", expanded=False):
        tm = metrics.get("training_metrics", {})
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**Training Period:** {metrics.get('training_period', 'N/A')}")
            st.write(f"**Data Range:** {tm.get('start_date', 'N/A')} → {tm.get('end_date', 'N/A')}")
        with c2:
            train_size = tm.get("train_size", 0)
            test_size = tm.get("test_size", 0)
            total = train_size + test_size
            if total > 0:
                st.write(f"**Split:** {train_size} Train / {test_size} Test")
                st.progress(train_size / total)
            else:
                st.write("**Split:** N/A")
        
        # Hyperparams or specifics
        if tm.get("best_params"):
            st.write("**Best Parameters:**")
            st.json(tm["best_params"])
        elif tm.get("sequence_length"):
            st.write(f"**Sequence Length:** {tm.get('sequence_length')}")
            st.write(f"**Hidden Size:** {tm.get('hidden_size')}")
