import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

import joblib
import numpy as np
import pandas as pd
from sqlmodel import Session, select
from sklearn.metrics import accuracy_score, mean_absolute_error, mean_squared_error, r2_score

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
    safe_symbol = ticker.replace(".", "_")
    model_name_base = f"{safe_symbol}_{model_type.lower()}"
    
    with Session(engine) as db:
        model_entry = ModelRegistryRepository.get_active_model(db, model_name_base)
        if not model_entry:
            raise ValueError(f"No active model found for {model_name_base}")

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
                .where(FeatureVector.symbol == ticker, FeatureVector.horizon == "short_term")
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
            
            # Get prices for labeling
            prices = db.exec(
                select(StockPrice)
                .where(StockPrice.symbol == ticker)
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
                        row["target"] = label
                        row["actual_price"] = price_series.iloc[curr_idx]
                        aligned.append(row)
                except: continue

            eval_df = pd.DataFrame(aligned)
            X = eval_df.drop(columns=["target", "actual_price", "current_close"], errors="ignore")
            # Alignment check
            if hasattr(model, "feature_names_in_"):
                X = X[model.feature_names_in_]
            
            y_true = eval_df["target"]
            y_prob = model.predict_proba(X)
            y_pred = model.predict(X)

            acc = accuracy_score(y_true, y_pred)
            # Directional Mask (ignore HOLD=1)
            mask = (y_true != 1)
            dir_acc = accuracy_score(y_true[mask], y_pred[mask]) if mask.sum() > 0 else acc

            return {
                "ticker": ticker,
                "model_type": "XGBoost (Classifier)",
                "accuracy": round(acc, 4),
                "directional_accuracy": round(dir_acc, 4),
                "data_points": len(eval_df),
                "predictions": [
                    {
                        "date": str(eval_df.index[i]), 
                        "actual": float(eval_df["actual_price"].iloc[i]),
                        "predicted": float(eval_df["actual_price"].iloc[i]), # Proxy for chart
                        "signal": "BUY" if y_pred[i]==2 else "AVOID" if y_pred[i]==0 else "HOLD",
                        "label": "BUY" if y_true[i]==2 else "AVOID" if y_true[i]==0 else "HOLD"
                    } for i in range(len(eval_df))
                ]
            }

        elif model_type.lower() == "prophet":
            # 1. Fetch Prices
            prices = db.exec(
                select(StockPrice)
                .where(StockPrice.symbol == ticker)
                .order_by(StockPrice.date.desc())
                .limit(200)
            ).all()
            
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
            mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100

            return {
                "ticker": ticker,
                "model_type": "Prophet (Time Series)",
                "MAE": round(mae, 2),
                "RMSE": round(rmse, 2),
                "MAPE": f"{mape:.2f}%",
                "data_points": len(df),
                "predictions": [
                    {"date": str(df["ds"].iloc[i].date()), "actual": float(y_true[i]), "predicted": float(y_pred[i])}
                    for i in range(len(df))
                ]
            }

    raise ValueError(f"Unsupported model type: {model_type}")
