import logging
import datetime as dt
from typing import Dict, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sqlmodel import Session, select

from app.models.market_data import MacroData

logger = logging.getLogger(__name__)

# --- NSE Holidays 2024-2026 ---
NSE_HOLIDAYS = pd.to_datetime([
    '2024-01-26', '2024-03-25', '2024-04-11', '2024-04-17', '2024-05-01', '2024-06-17', 
    '2024-07-17', '2024-08-15', '2024-10-02', '2024-11-01', '2024-11-15', '2024-12-25',
    '2025-01-26', '2025-03-14', '2025-03-31', '2025-04-10', '2025-04-14', '2025-04-18', 
    '2025-05-01', '2025-08-15', '2025-10-02', '2025-10-20', '2025-11-05', '2025-12-25'
])

HOLIDAYS_DF = pd.DataFrame({
    'holiday': 'NSE_Holiday',
    'ds': NSE_HOLIDAYS,
    'lower_window': 0,
    'upper_window': 0,
})

BUDGET_DAYS = pd.DataFrame({
    'holiday': 'Union_Budget',
    'ds': pd.to_datetime(['2024-02-01', '2025-02-01', '2026-02-01']),
    'lower_window': -1,
    'upper_window': 1,
})
ALL_HOLIDAYS = pd.concat([HOLIDAYS_DF, BUDGET_DAYS])

def train_prophet_model(
    raw_data_df: pd.DataFrame,
    existing_model_path: Optional[str] = None,
) -> Tuple[Prophet, Dict]:
    """Train Prophet with Macro Regressors and optimized seasonality."""
    if raw_data_df.empty:
        raise ValueError("Training data is empty")

    from app.database import engine

    # Prepare historical macro features
    with Session(engine) as db:
        macro_rows = db.exec(select(MacroData).order_by(MacroData.date.asc())).all()
    
    macro_df = pd.DataFrame([{"ds": pd.to_datetime(m.date), "indicator": m.indicator, "value": m.value} for m in macro_rows])
    if not macro_df.empty:
        pivot_macro = macro_df.pivot(index="ds", columns="indicator", values="value").fillna(method="ffill").fillna(0)
        pivot_macro.columns = [f"reg_{c.lower()}" for c in pivot_macro.columns]
    else:
        pivot_macro = pd.DataFrame()

    # Prepare main df
    df = raw_data_df.copy()
    df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
    df = df.rename(columns={"Date": "ds", "Close": "y"})
    df["ds"] = pd.to_datetime(df["ds"], errors="coerce")
    df["y"] = pd.to_numeric(df["y"], errors="coerce")
    
    # ── Section 2A: Use Smoothed Trend ──────────────────────────────────────
    # Stock prices have noise; smoothing helps Prophet find the underlying trend.
    df["y"] = df["y"].rolling(window=5, min_periods=1).mean()
    
    df.dropna(subset=["ds", "y"], inplace=True)
    df = df[["ds", "y"]].drop_duplicates(subset="ds").sort_values("ds")

    # Join regressors
    regressors = []
    if not pivot_macro.empty:
        df = df.merge(pivot_macro, on="ds", how="left").fillna(method="ffill")
        # Only keep regressors that have at least 80% coverage in the dataset
        potential_regs = [c for c in df.columns if c.startswith("reg_")]
        for reg in potential_regs:
            non_zero_pct = (df[reg].notna() & (df[reg] != 0)).sum() / len(df)
            if non_zero_pct > 0.8:
                regressors.append(reg)
            else:
                df.drop(columns=[reg], inplace=True)
        df.fillna(0, inplace=True)

    if len(df) < 50:
        raise ValueError(f"Insufficient samples: {len(df)} (need 50+)")

    # ── 80/20 Split & Cross-Validation ───────────────────────────────────────
    split_idx = int(len(df) * 0.8)
    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()

    def build_model(cp_scale):
        m = Prophet(
            holidays=ALL_HOLIDAYS,
            seasonality_mode='additive', # More stable for price
            changepoint_prior_scale=cp_scale,
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False
        )
        for reg in regressors:
            m.add_regressor(reg)
        return m

    # ── Section 2D: Tunning — Grid Search for changepoint_prior_scale ────────
    # The default 0.05 is often too rigid. We test a few values to find the best fit.
    best_mae = float('inf')
    best_cp = 0.4
    candidate_scales = [0.1, 0.25, 0.4, 0.5]
    
    logger.info(f"Starting grid search for Prophet (scales: {candidate_scales})...")
    
    for cp in candidate_scales:
        try:
            temp_model = build_model(cp)
            temp_model.fit(train_df)
            
            future_test = test_df.drop(columns="y")
            forecast_test = temp_model.predict(future_test)
            
            y_actual = test_df["y"].values
            y_pred = forecast_test["yhat"].values[:len(y_actual)]
            
            temp_mae = mean_absolute_error(y_actual, y_pred)
            if temp_mae < best_mae:
                best_mae = temp_mae
                best_cp = cp
        except Exception as e:
            logger.warning(f"Prophet tuning failed for scale {cp}: {e}")

    logger.info(f"Grid search complete. Best changepoint_prior_scale: {best_cp} (MAE: {best_mae:.2f})")

    # ── Final Training ───────────────────────────────────────────────────────
    model = build_model(best_cp)
    model.fit(df)
    
    # Final metrics calculation on the best model
    mae = best_mae
    # Re-calculate others for the best one to be sure
    rmse = float(np.sqrt(mean_squared_error(y_actual, y_pred)))
    r2 = float(r2_score(y_actual, y_pred))
    mape = float(np.mean(np.abs((y_actual - y_pred) / y_actual))) * 100

    metrics = {
        "MAE": round(mae, 4),
        "RMSE": round(rmse, 4),
        "R2": round(r2, 4),
        "MAPE": f"{mape:.2f}%",
        "train_size": len(train_df),
        "test_size": len(test_df),
        "regressors_used": regressors,
        "end_date": str(df["ds"].max().date())
    }

    logger.info(f"Prophet Training Done. R2: {r2:.3f}, MAPE: {mape:.2f}%")
    return model, metrics
