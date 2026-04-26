import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

import joblib
import numpy as np
import pandas as pd
from sqlmodel import Session, select
from sklearn.metrics import accuracy_score, mean_absolute_error, mean_squared_error, r2_score, classification_report, confusion_matrix

from app.database import engine
from app.repositories.model_registry_repository import ModelRegistryRepository
from app.models.feature_data import FeatureVector
from app.models.stock_data import StockPrice
from app.models.market_data import MacroData

logger = logging.getLogger(__name__)

def evaluate_model(ticker: str, period: str, model_type: str) -> Dict[str, Any]:
    """
    Evaluates the active model using the modern training/inference patterns.
    """
    original_ticker = ticker.replace("_", ".")
    safe_symbol = ticker.replace(".", "_")
    model_name_base = f"{safe_symbol}_{model_type.lower()}"
    
    with Session(engine) as db:
        model_entry = ModelRegistryRepository.get_active_model(db, model_name_base)
        if not model_entry:
            raise ValueError(f"No active model found for {model_name_base}")

        if model_type.lower() == "lstm":
            # LSTM specialized stored-metrics-only
            model_metrics = model_entry.metrics or {}
            accuracy = model_metrics.get("accuracy", 0.0)
            dir_acc = model_metrics.get("directional_accuracy", accuracy)

            return {
                "ticker": ticker,
                "model_type": "LSTM (Sequence Classifier)",
                "model_category": "classification",
                "accuracy_pct": round(float(accuracy) * 100, 1),
                "directional_accuracy": round(float(dir_acc), 4),
                "data_points": model_metrics.get("test_size", 0),
                "trained_on": str(model_entry.trained_at.date()),
                "training_period": model_entry.training_period or "5y",
                "training_metrics": model_metrics,
                "predictions": [],
                "eval_status": "stored_metrics_only",
                "MAE": None, "RMSE": None, "R2": None, "MAPE": None,
                "feature_importance": None,
            }

        # For XGBoost and Prophet, we load the model for evaluation
        model_path = model_entry.file_path
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file missing: {model_path}")

        bundle = joblib.load(model_path)
        model = bundle["model"] if isinstance(bundle, dict) else bundle

        # --- EVALUATION LOGIC BY TYPE ---
        
        if model_type.lower() == "xgboost":
            # 1. Fetch data for evaluation (last 200 days)
            fvs = db.exec(
                select(FeatureVector)
                .where(FeatureVector.symbol == original_ticker, FeatureVector.horizon == "short_term")
                .order_by(FeatureVector.date.desc())
                .limit(200)
            ).all()

            if len(fvs) < 50:
                raise ValueError(f"Insufficient history for evaluation: {len(fvs)} rows")

            data = []
            for fv in fvs:
                row = fv.features.copy()
                row["date"] = fv.date
                data.append(row)

            df = pd.DataFrame(data).set_index("date").sort_index()
            df.index = pd.to_datetime(df.index)
            
            # Get prices for labeling
            prices = db.exec(
                select(StockPrice)
                .where(StockPrice.symbol == original_ticker)
                .order_by(StockPrice.date.asc())
            ).all()
            price_series = pd.Series({pd.to_datetime(p.date): p.close for p in prices})

            # Align for 5d horizon
            aligned = []
            horizon = 5
            for d in df.index:
                try:
                    curr_idx = price_series.index.get_loc(d)
                    if curr_idx + horizon < len(price_series):
                        ret = (price_series.iloc[curr_idx + horizon] - price_series.iloc[curr_idx]) / price_series.iloc[curr_idx]
                        label = 1
                        if ret > 0.02: label = 2
                        elif ret < -0.02: label = 0
                        
                        row = df.loc[d].to_dict()
                        row["date"] = d
                        row["target"] = label
                        row["actual_price"] = price_series.iloc[curr_idx]
                        aligned.append(row)
                except: continue

            eval_df = pd.DataFrame(aligned)
            if eval_df.empty:
                raise ValueError(f"Could not align feature vectors with price history for {original_ticker}. Check if data is synchronized.")

            X = eval_df.drop(columns=["target", "actual_price", "current_close", "date"], errors="ignore")
            # Alignment check - Use reindex to be robust against missing columns in eval set
            if hasattr(model, "feature_names_in_"):
                X = X.reindex(columns=model.feature_names_in_, fill_value=0.0)
            
            y_true = eval_df["target"]
            y_pred = model.predict(X)

            acc = accuracy_score(y_true, y_pred)
            # Directional Mask (ignore HOLD=1)
            mask = (y_true != 1)
            dir_acc = accuracy_score(y_true[mask], y_pred[mask]) if mask.sum() > 0 else acc

            # Per-class metrics
            report = classification_report(y_true, y_pred, 
                                           labels=[0, 1, 2],
                                           target_names=["AVOID", "HOLD", "BUY"],
                                           output_dict=True, zero_division=0)
            
            precision_per_class = {k: round(float(v["precision"]), 4) for k, v in report.items() if k in ["AVOID", "HOLD", "BUY"]}
            recall_per_class = {k: round(float(v["recall"]), 4) for k, v in report.items() if k in ["AVOID", "HOLD", "BUY"]}
            f1_per_class = {k: round(float(v["f1-score"]), 4) for k, v in report.items() if k in ["AVOID", "HOLD", "BUY"]}

            # Confusion Matrix
            cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2])
            confusion_data = {
                "labels": ["AVOID", "HOLD", "BUY"],
                "matrix": cm.tolist()
            }

            # Feature Importance
            feat_imp = {"Feature": list(X.columns), "Weight": [0.0] * len(X.columns)}
            if hasattr(model, "feature_importances_"):
                feat_imp["Weight"] = [round(float(w), 4) for w in model.feature_importances_]
            elif hasattr(model, "get_score"): # XGBoost Booster direct access
                scores = model.get_score(importance_type="weight")
                feat_imp["Weight"] = [round(float(scores.get(c, 0)), 4) for c in X.columns]

            return {
                "ticker": ticker,
                "model_type": "XGBoost (Classifier)",
                "model_category": "classification",
                "accuracy_pct": round(acc * 100, 1),
                "directional_accuracy": round(float(dir_acc), 4),
                "data_points": len(eval_df),
                "trained_on": str(model_entry.trained_at.date()),
                "training_period": model_entry.training_period,
                "training_metrics": model_entry.metrics,
                "predictions": [
                    {
                        "date": eval_df["date"].iloc[i].strftime("%Y-%m-%d"), 
                        "actual": float(eval_df["actual_price"].iloc[i]),
                        "predicted": float(eval_df["actual_price"].iloc[i]), # Proxy for chart
                        "signal": "BUY" if y_pred[i]==2 else "AVOID" if y_pred[i]==0 else "HOLD",
                        "label": "BUY" if y_true[i]==2 else "AVOID" if y_true[i]==0 else "HOLD"
                    } for i in range(len(eval_df))
                ],
                "eval_status": "live",
                "precision_per_class": precision_per_class,
                "recall_per_class": recall_per_class,
                "f1_per_class": f1_per_class,
                "confusion_matrix": confusion_data,
                "MAE": None, "RMSE": None, "R2": None, "MAPE": None,
                "feature_importance": feat_imp
            }

        elif model_type.lower() == "prophet":
            # 1. Fetch Prices
            prices = db.exec(
                select(StockPrice)
                .where(StockPrice.symbol == original_ticker)
                .order_by(StockPrice.date.desc())
                .limit(200)
            ).all()
            
            if not prices:
                raise ValueError(f"Insufficient history for evaluation: 0 rows for {original_ticker}")
            
            df = pd.DataFrame([{"ds": pd.to_datetime(p.date), "y": p.close} for p in prices]).sort_values("ds")
            
            # 2. Add Regressors
            if model.extra_regressors:
                macro_rows = db.exec(select(MacroData).order_by(MacroData.date.asc())).all()
                macro_df = pd.DataFrame([{"ds": pd.to_datetime(m.date), "indicator": m.indicator, "value": m.value} for m in macro_rows])
                if not macro_df.empty:
                    pivot = macro_df.pivot(index="ds", columns="indicator", values="value").fillna(method="ffill")
                    pivot.columns = [f"reg_{c.lower()}" for c in pivot.columns]
                    df = df.merge(pivot, on="ds", how="left").fillna(method="ffill")

            # 3. Forecast
            future = df.drop(columns="y")
            forecast = model.predict(future)
            
            y_true = df["y"].values
            y_pred = forecast["yhat"].values
            
            mae = mean_absolute_error(y_true, y_pred)
            rmse = np.sqrt(mean_squared_error(y_true, y_pred))
            r2 = r2_score(y_true, y_pred)
            mape = float(np.mean(np.abs((y_true - y_pred) / y_true)) * 100)

            # Directional Accuracy (Phase 1 enhancement)
            direction_actual = np.diff(y_true) > 0
            direction_pred = np.diff(y_pred) > 0
            dir_acc = np.mean(direction_actual == direction_pred) if len(direction_actual) > 0 else 0.0

            return {
                "ticker": ticker,
                "model_type": "Prophet (Time Series)",
                "model_category": "regression",
                "accuracy_pct": round(dir_acc * 100, 1),
                "directional_accuracy": round(float(dir_acc), 4),
                "MAE": round(mae, 2),
                "RMSE": round(rmse, 2),
                "R2": round(r2, 4),
                "MAPE": round(mape, 2),
                "data_points": len(df),
                "trained_on": str(model_entry.trained_at.date()),
                "training_period": model_entry.training_period,
                "training_metrics": model_entry.metrics,
                "predictions": [
                    {
                        "date": str(df["ds"].iloc[i].date()), 
                        "actual": float(y_true[i]), 
                        "predicted": float(y_pred[i]),
                        "lower_bound": float(forecast["yhat_lower"].iloc[i]),
                        "upper_bound": float(forecast["yhat_upper"].iloc[i])
                    }
                    for i in range(len(df))
                ],
                "eval_status": "live",
                "feature_importance": None # Prophet doesn't natively expose feature weights like XGB
            }

    raise ValueError(f"Unsupported model type: {model_type}")
