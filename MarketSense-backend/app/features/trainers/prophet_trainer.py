import logging
from typing import Dict, Optional, Tuple

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
    'lower_window': -3,
    'upper_window': 2,
})
ALL_HOLIDAYS = pd.concat([HOLIDAYS_DF, BUDGET_DAYS])

def prepare_prophet_data(df: pd.DataFrame) -> pd.DataFrame:
    """Standardized data preparation for Prophet (Renaming, Cleaning, Log-Smoothing)."""
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    col_map = {c.lower(): c for c in df.columns}
    rename_targets = {}
    if "date" in col_map: rename_targets[col_map["date"]] = "ds"
    if "close" in col_map: rename_targets[col_map["close"]] = "y"
    
    if "ds" not in rename_targets and df.index.name and df.index.name.lower() == "date":
        df = df.reset_index()
        col_map = {c.lower(): c for c in df.columns}
        if "date" in col_map: rename_targets[col_map["date"]] = "ds"

    df = df.rename(columns=rename_targets)
    if "ds" not in df.columns: df = df.rename(columns={df.columns[0]: "ds"})

    df["ds"] = pd.to_datetime(df["ds"], errors="coerce").dt.tz_localize(None)
    if "y" not in df.columns:
        potential_y = [c for c in df.columns if 'close' in c.lower() or 'adj' in c.lower()]
        if potential_y: df = df.rename(columns={potential_y[0]: "y"})
    
    df["y"] = pd.to_numeric(df.get("y", 0), errors="coerce")
    df["y"] = df["y"].rolling(window=5, min_periods=1).mean()
    df["y"] = np.log1p(df["y"]) 
    
    df.dropna(subset=["ds", "y"], inplace=True)
    return df.sort_values("ds")

def extract_prophet_signals(model: Prophet, raw_df: pd.DataFrame) -> pd.DataFrame:
    """Extract trend signals from a trained Prophet model for meta-learner."""
    from app.database import engine
    df = prepare_prophet_data(raw_df)
    
    if model.extra_regressors:
        with Session(engine) as db:
            macro_rows = db.exec(select(MacroData).order_by(MacroData.date.asc())).all()
        
        macro_df = pd.DataFrame([{"ds": pd.to_datetime(m.date), "indicator": m.indicator, "value": m.value} for m in macro_rows])
        if not macro_df.empty:
            pivot_macro = macro_df.pivot(index="ds", columns="indicator", values="value").ffill().fillna(0)
            pivot_macro.columns = [f"reg_{c.lower()}" for c in pivot_macro.columns]
            df = df.merge(pivot_macro, on="ds", how="left").ffill().fillna(0)

    forecast = model.predict(df)
    signals = pd.DataFrame({
        "date": forecast["ds"],
        "prophet_trend_dir": np.sign(forecast["trend"].diff().fillna(0)),
        "prophet_trend_strength": forecast["trend"].diff().abs().fillna(0),
        "prophet_uncertainty": forecast["yhat_upper"] - forecast["yhat_lower"],
    })
    return signals


def train_prophet_model(
    raw_data_df: pd.DataFrame,
    existing_model_path: Optional[str] = None,
) -> Tuple[Prophet, Dict]:
    """Train Prophet with Macro Regressors and boundary search for speed (Phase 3)."""
    if raw_data_df.empty: raise ValueError("Training data is empty")

    from app.database import engine
    with Session(engine) as db:
        macro_rows = db.exec(select(MacroData).order_by(MacroData.date.asc())).all()
    
    macro_df = pd.DataFrame([{"ds": pd.to_datetime(m.date), "indicator": m.indicator, "value": m.value} for m in macro_rows])
    if not macro_df.empty:
        pivot_macro = macro_df.pivot(index="ds", columns="indicator", values="value").ffill().fillna(0)
        pivot_macro.columns = [f"reg_{c.lower()}" for c in pivot_macro.columns]
    else:
        pivot_macro = pd.DataFrame()

    df = prepare_prophet_data(raw_data_df)
    regressors = []
    if not pivot_macro.empty:
        df = df.merge(pivot_macro, on="ds", how="left").ffill()
        for reg in [c for c in df.columns if c.startswith("reg_")]:
            if (df[reg].notna() & (df[reg] != 0)).sum() / len(df) > 0.8: regressors.append(reg)
            else: df.drop(columns=[reg], inplace=True)
        df.fillna(0, inplace=True)

    if len(df) < 50: raise ValueError(f"Insufficient samples: {len(df)}")

    split_idx = int(len(df) * 0.8)
    train_df, test_df = df.iloc[:split_idx].copy(), df.iloc[split_idx:].copy()

    def build_model(cp_scale, s_scale):
        m = Prophet(holidays=ALL_HOLIDAYS, seasonality_mode='multiplicative', 
                    changepoint_prior_scale=cp_scale, seasonality_prior_scale=s_scale,
                    yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False)
        m.add_seasonality(name='results_season', period=91.25, fourier_order=3)
        for reg in regressors: m.add_regressor(reg)
        return m

    # Boundary search (4 combinations instead of 12 for speed)
    best_mae, best_cp, best_ss, best_metrics = float('inf'), 0.1, 10.0, {}
    candidate_cp, candidate_ss = [0.05, 0.5], [1.0, 10.0]
    
    logger.info(f"Refined boundary search for Prophet...")
    for cp in candidate_cp:
        for ss in candidate_ss:
            try:
                temp_model = build_model(cp, ss).fit(train_df)
                forecast_test = temp_model.predict(test_df.drop(columns="y"))
                y_actual, y_pred = np.expm1(test_df["y"].values), np.expm1(forecast_test["yhat"].values[:len(test_df)])
                mae = mean_absolute_error(y_actual, y_pred)
                if mae < best_mae:
                    best_mae, best_cp, best_ss = mae, cp, ss
                    best_metrics = {"MAE": round(mae, 4), "RMSE": round(float(np.sqrt(mean_squared_error(y_actual, y_pred))), 4),
                                    "R2": round(float(r2_score(y_actual, y_pred)), 4), "MAPE": f"{(np.mean(np.abs((y_actual - y_pred) / (y_actual + 1e-9))) * 100):.2f}%"}
            except Exception as e: logger.warning(f"Prophet tuning failed: {e}")

    model = build_model(best_cp, best_ss).fit(df)
    metrics = {**best_metrics, "train_size": len(train_df), "test_size": len(test_df), 
               "regressors_used": regressors, "best_cp": best_cp, "best_ss": best_ss, 
               "end_date": str(df["ds"].max().date()), "supports_trend_signals": True}

    logger.info(f"Prophet Phase 3 Done. R2: {best_metrics.get('R2')}")
    return model, metrics
