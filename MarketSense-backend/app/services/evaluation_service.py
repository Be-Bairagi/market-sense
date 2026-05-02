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

import torch
from app.features.trainers.prophet_trainer import extract_prophet_signals

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
        model = bundle.get("model") if isinstance(bundle, dict) else bundle

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

        elif model_type.lower() == "hybrid":
            # Hybrid models are stored as a bundle dictionary
            if not isinstance(bundle, dict):
                raise ValueError("Corrupt hybrid model: expected bundle dictionary")
            
            xgb_m = bundle["xgb_model"]
            lstm_bundle = bundle["lstm_bundle"]
            prophet_m = bundle["prophet_model"]
            meta_m = bundle["meta_learner"]
            
            # 1. Generic Feature Fetching
            fvs = db.exec(
                select(FeatureVector)
                .where(FeatureVector.symbol == original_ticker, FeatureVector.horizon == "short_term")
                .order_by(FeatureVector.date.desc())
                .limit(100) # Recent 100 days for live eval
            ).all()

            if len(fvs) < 50:
                raise ValueError(f"Insufficient history for hybrid evaluation: {len(fvs)} rows")

            data = []
            for fv in fvs:
                row = fv.features.copy()
                row["date"] = pd.to_datetime(fv.date)
                data.append(row)

            features_df = pd.DataFrame(data).set_index("date").sort_index()
            features_df.index = pd.to_datetime(features_df.index).normalize()
            features_df = features_df[~features_df.index.duplicated(keep="last")]
            features_df = features_df.apply(pd.to_numeric, errors='coerce').fillna(0)
            
            prices = db.exec(select(StockPrice).where(StockPrice.symbol == original_ticker).order_by(StockPrice.date.asc())).all()
            price_series = pd.Series({pd.to_datetime(p.date): p.close for p in prices}).sort_index()
            price_series.index = pd.to_datetime(price_series.index).normalize()
            
            # Prophet signals - requires raw data for regressors
            from app.services.fetch_data_service import FetchDataService
            fetch_svc = FetchDataService()
            raw_data = fetch_svc.fetch_stock_data(original_ticker, period="1y", interval="1d", raw=True)
            prophet_signals = extract_prophet_signals(prophet_m, raw_data)
            prophet_signals["date"] = pd.to_datetime(prophet_signals["date"]).dt.tz_localize(None).dt.normalize()
            prophet_signals.set_index("date", inplace=True)

            # 2. Reconstruct Meta-Features
            meta_rows = []
            eval_indices = []
            
            from app.features.trainers.lstm_trainer import HybridStockModel
            lstm_m = HybridStockModel(**lstm_bundle["model_config"])
            lstm_m.load_state_dict(lstm_bundle["model_state"])
            lstm_m.eval()
            
            lstm_scaler = lstm_bundle["scaler"]
            lstm_feats_in = lstm_bundle["features_in"]
            seq_len = lstm_bundle["seq_length"]
            
            for d in features_df.index:
                try:
                    curr_idx = price_series.index.get_loc(d)
                    if curr_idx + 5 >= len(price_series): continue
                    
                    # Target
                    ret = (price_series.iloc[curr_idx + 5] - price_series.iloc[curr_idx]) / price_series.iloc[curr_idx]
                    label = 1
                    if ret > 0.02: label = 2
                    elif ret < -0.02: label = 0
                    
                    # XGB
                    xgb_cols = xgb_m.feature_names_in_ if hasattr(xgb_m, 'feature_names_in_') else xgb_m.estimator.feature_names_in_
                    xgb_x = features_df.loc[[d]].reindex(columns=xgb_cols, fill_value=0.0)
                    xgb_probs = xgb_m.predict_proba(xgb_x)[0]
                    
                    # LSTM
                    row_idx = features_df.index.get_loc(d)
                    if isinstance(row_idx, (slice, np.ndarray)):
                        row_idx = row_idx[0] if isinstance(row_idx, np.ndarray) else row_idx.start

                    if row_idx < seq_len: continue
                    seq_feats = features_df.iloc[row_idx - seq_len : row_idx].reindex(columns=lstm_feats_in, fill_value=0.0).values
                    seq_scaled = lstm_scaler.transform(seq_feats).reshape(1, seq_len, -1)
                    lstm_m.eval()
                    with torch.no_grad():
                        out = lstm_m(torch.FloatTensor(seq_scaled))
                        lstm_probs = torch.softmax(out, dim=1).numpy()[0]
                    
                    # Prophet
                    p_row = prophet_signals.loc[d]
                    
                    meta_rows.append({
                        "xgb_p0": float(xgb_probs[0]), "xgb_p1": float(xgb_probs[1]), "xgb_p2": float(xgb_probs[2]),
                        "lstm_p0": float(lstm_probs[0]), "lstm_p1": float(lstm_probs[1]), "lstm_p2": float(lstm_probs[2]),
                        "p_dir": float(p_row["prophet_trend_dir"]),
                        "p_strength": float(p_row["prophet_trend_strength"]),
                        "p_uncertainty": float(p_row["prophet_uncertainty"]),
                        "rsi": float(features_df.loc[d, "rsi_14"] if "rsi_14" in features_df.columns else 50),
                        "vol": float(features_df.loc[d, "volatility_30d"] if "volatility_30d" in features_df.columns else 0),
                    })
                    eval_indices.append({"date": d, "target": label, "actual_price": price_series.iloc[curr_idx]})
                except: continue

            if not meta_rows:
                raise ValueError("Failed to align meta-features for hybrid evaluation.")

            X_meta = pd.DataFrame(meta_rows)
            y_true = [r["target"] for r in eval_indices]
            y_pred = meta_m.predict(X_meta)
            
            acc = accuracy_score(y_true, y_pred)
            mask = np.array(y_true) != 1
            dir_acc = accuracy_score(np.array(y_true)[mask], y_pred[mask]) if mask.sum() > 0 else acc

            # Per-class metrics
            report = classification_report(y_true, y_pred, labels=[0, 1, 2], output_dict=True, zero_division=0)
            
            return {
                "ticker": ticker,
                "model_type": "Hybrid Stacking Ensemble",
                "model_category": "classification",
                "accuracy_pct": round(acc * 100, 1),
                "directional_accuracy": round(float(dir_acc), 4),
                "data_points": len(y_true),
                "trained_on": str(model_entry.trained_at.date()),
                "training_period": model_entry.training_period,
                "training_metrics": model_entry.metrics,
                "predictions": [
                    {
                        "date": eval_indices[i]["date"].strftime("%Y-%m-%d"),
                        "actual": float(eval_indices[i]["actual_price"]),
                        "predicted": float(eval_indices[i]["actual_price"]),
                        "signal": "BUY" if y_pred[i]==2 else "AVOID" if y_pred[i]==0 else "HOLD",
                        "label": "BUY" if y_true[i]==2 else "AVOID" if y_true[i]==0 else "HOLD"
                    } for i in range(len(y_true))
                ],
                "eval_status": "live",
                "precision_per_class": {
                    "AVOID": round(float(report["0"]["precision"]), 4),
                    "HOLD": round(float(report["1"]["precision"]), 4),
                    "BUY": round(float(report["2"]["precision"]), 4)
                },
                "recall_per_class": {
                    "AVOID": round(float(report["0"]["recall"]), 4),
                    "HOLD": round(float(report["1"]["recall"]), 4),
                    "BUY": round(float(report["2"]["recall"]), 4)
                },
                "f1_per_class": {
                    "AVOID": round(float(report["0"]["f1-score"]), 4),
                    "HOLD": round(float(report["1"]["f1-score"]), 4),
                    "BUY": round(float(report["2"]["f1-score"]), 4)
                },
                "confusion_matrix": {"labels": ["AVOID", "HOLD", "BUY"], "matrix": confusion_matrix(y_true, y_pred, labels=[0,1,2]).tolist()},
                "MAE": None, "RMSE": None, "R2": None, "MAPE": None,
                "feature_importance": {
                    "Feature": list(X_meta.columns), 
                    "Weight": [round(float(w), 4) for w in (meta_m.feature_importances_ if hasattr(meta_m, "feature_importances_") else np.abs(meta_m.coef_).mean(axis=0))]
                }
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
