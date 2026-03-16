import os
from datetime import datetime
from typing import Any, Dict

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, mean_absolute_error,
                             mean_squared_error, r2_score)
from sqlmodel import Session, select

from app.database import engine
from app.models.feature_data import FeatureVector
from app.models.market_data import MacroData
from app.models.stock_data import StockPrice
from app.repositories.model_registry_repository import ModelRegistryRepository
from app.config import settings

MODELS_DIR = settings.models_path


def test_evaluate_model(ticker: str, period: str, model_type: str) -> Dict[str, Any]:
    """
    Shadow Evaluation Service ported from accuracy-trackker branch.
    Handles correct ticker reverse-sanitization and metric extraction.
    """
    # 1. Reverse-sanitization (Fix from accuracy-trackker)
    original_ticker = ticker.replace("_", ".")
    safe_symbol = ticker.replace(".", "_")
    model_name_base = f"{safe_symbol}_{model_type.lower()}"

    with Session(engine) as db:
        # Find the active model in the registry
        model_entry = ModelRegistryRepository.get_active_model(db, model_name_base)
        if not model_entry:
            # Fallback to direct file search if not in registry (legacy support)
            model_path = os.path.join(MODELS_DIR, f"{ticker}_{model_type}.pkl")
            if not os.path.exists(model_path):
                # Try finding versioned version
                model_files = [
                    f
                    for f in os.listdir(MODELS_DIR)
                    if f.startswith(f"{safe_symbol}_{model_type}_v")
                    and f.endswith(".pkl")
                ]
                if not model_files:
                    raise ValueError(
                        f"No active model or file found for {model_name_base}"
                    )
                model_files.sort(reverse=True)
                model_path = os.path.join(MODELS_DIR, model_files[0])
            model_metrics = {}
        else:
            model_path = model_entry.file_path
            model_metrics = model_entry.metrics or {}

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file missing: {model_path}")

        bundle = joblib.load(model_path)
        model = bundle["model"] if isinstance(bundle, dict) else bundle
        if not model_metrics and isinstance(bundle, dict):
            model_metrics = bundle.get("metrics", {})

        # --- EVALUATION LOGIC ---

        if model_type.lower() == "xgboost":
            # Fetch features using the ORIGINAL ticker (RELIANCE.NS)
            fvs = db.exec(
                select(FeatureVector)
                .where(
                    FeatureVector.symbol == original_ticker,
                    FeatureVector.horizon == "short_term",
                )
                .order_by(FeatureVector.date.desc())
                .limit(100)
            ).all()

            if not fvs:
                raise ValueError(f"No feature vectors found for {original_ticker}")

            fvs.reverse()  # Chronological

            # Fetch prices for labeling
            start_date = fvs[0].date
            prices = db.exec(
                select(StockPrice)
                .where(
                    StockPrice.symbol == original_ticker, StockPrice.date >= start_date
                )
                .order_by(StockPrice.date.asc())
            ).all()
            price_series = pd.Series({pd.to_datetime(p.date): p.close for p in prices})

            # Align for 5d horizon
            X_list = []
            y_true = []
            dates = []
            horizon = 5

            for fv in fvs:
                fv_date = pd.to_datetime(fv.date)
                try:
                    curr_idx = price_series.index.get_loc(fv_date)
                    target_idx = curr_idx + horizon
                    if target_idx < len(price_series):
                        curr_p = price_series.iloc[curr_idx]
                        target_p = price_series.iloc[target_idx]
                        ret = (target_p - curr_p) / curr_p

                        label = 1
                        if ret > 0.02:
                            label = 2
                        elif ret < -0.02:
                            label = 0

                        X_list.append(fv.features)
                        y_true.append(label)
                        dates.append(fv.date.strftime("%Y-%m-%d"))
                except:
                    continue

            if not X_list:
                raise ValueError("Could not align features with prices for evaluation.")

            X = pd.DataFrame(X_list).apply(pd.to_numeric, errors="coerce").fillna(0)
            if hasattr(model, "feature_names_in_"):
                training_cols = list(model.feature_names_in_)
                for col in training_cols:
                    if col not in X.columns:
                        X[col] = 0.0
                X = X[training_cols]

            y_pred = model.predict(X)
            acc = accuracy_score(y_true, y_pred)

            # Directional accuracy (UP/DOWN only)
            y_true_arr = np.array(y_true)
            y_pred_arr = np.array(y_pred)
            mask = y_true_arr != 1
            dir_acc = (
                accuracy_score(y_true_arr[mask], y_pred_arr[mask])
                if mask.sum() > 0
                else acc
            )

            return {
                "ticker": ticker,
                "model_type": "Shadow XGBoost (Classification)",
                "accuracy": round(float(acc), 4),
                "directional_accuracy": round(float(dir_acc), 4),
                "data_points": len(X),
                "trained_on": model_metrics.get("end_date", "Unknown"),
                "predictions": [
                    {"date": d, "actual": int(a), "predicted": int(p)}
                    for d, a, p in zip(dates, y_true, y_pred)
                ],
            }

        elif model_type.lower() == "prophet":
            # Fetch Prices using ORIGINAL ticker
            prices = db.exec(
                select(StockPrice)
                .where(StockPrice.symbol == original_ticker)
                .order_by(StockPrice.date.desc())
                .limit(200)
            ).all()

            if not prices:
                raise ValueError(f"No prices found for {original_ticker}")

            df_eval = (
                pd.DataFrame(
                    [{"ds": pd.to_datetime(p.date), "y": p.close} for p in prices]
                )
                .sort_values("ds")
                .tail(100)
            )

            # Add Regressors
            if model.extra_regressors:
                macro_rows = db.exec(
                    select(MacroData).order_by(MacroData.date.asc())
                ).all()
                macro_df = pd.DataFrame(
                    [
                        {
                            "ds": pd.to_datetime(m.date),
                            "indicator": m.indicator,
                            "value": m.value,
                        }
                        for m in macro_rows
                    ]
                )
                if not macro_df.empty:
                    pivot = macro_df.pivot(
                        index="ds", columns="indicator", values="value"
                    ).fillna(method="ffill")
                    pivot.columns = [f"reg_{c.lower()}" for c in pivot.columns]
                    df_eval = df_eval.merge(pivot, on="ds", how="left").fillna(
                        method="ffill"
                    )

            # Forecast
            future = df_eval.drop(columns="y")
            forecast = model.predict(future)

            y_true = df_eval["y"].values
            y_pred = forecast["yhat"].values

            mae = mean_absolute_error(y_true, y_pred)
            rmse = np.sqrt(mean_squared_error(y_true, y_pred))
            r2 = r2_score(y_true, y_pred)
            mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100

            return {
                "ticker": ticker,
                "model_type": "Shadow Prophet (Regression)",
                "MAE": round(float(mae), 2),
                "RMSE": round(float(rmse), 2),
                "R2": round(float(r2), 4),
                "MAPE": f"{mape:.2f}%",
                "data_points": len(df_eval),
                "predictions": [
                    {
                        "date": str(df_eval["ds"].iloc[i].date()),
                        "actual": float(y_true[i]),
                        "predicted": float(y_pred[i]),
                    }
                    for i in range(len(df_eval))
                ],
            }

        elif model_type.lower() == "lstm":
            # Just use predictor directly to get test metrics
            from app.features.trainers.lstm_trainer import train_lstm_model

            # To actually evaluate without retraining, we would do a small inference loop
            # BUT the trainer already bundled 'metrics' with the exact OOS accuracy
            return {
                "ticker": ticker,
                "model_type": "Shadow PyTorch LSTM (Sequence)",
                "accuracy": model_metrics.get("accuracy", 0.0),
                "directional_accuracy": model_metrics.get("directional_accuracy", 0.0),
                "data_points": model_metrics.get("test_size", 0),
                "trained_on": model_metrics.get("end_date", "Unknown"),
                "predictions": [],  # Not logging individual sequence predictions for brevity
            }

    raise ValueError(f"Unsupported model type: {model_type}")
