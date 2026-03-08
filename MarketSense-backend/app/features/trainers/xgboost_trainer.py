import logging
from datetime import timedelta
from typing import Dict, Tuple

import numpy as np
import pandas as pd
import xgboost as xgb
from sqlmodel import Session, select
from sklearn.metrics import accuracy_score, classification_report, mean_absolute_error
from sklearn.model_selection import train_test_split

from app.models.feature_data import FeatureVector
from app.models.stock_data import StockPrice

logger = logging.getLogger(__name__)


def train_xgboost_model(symbol: str, horizon_days: int = 5) -> Tuple[xgb.XGBClassifier, Dict]:
    """
    Trains an XGBoost model for a symbol using historical feature vectors.
    Target: Price direction (BUY/HOLD/AVOID) after `horizon_days`.
    """
    from app.database import engine

    with Session(engine) as db:
        # 1. Fetch all feature vectors (Filter for short_term horizon)
        fvs = db.exec(
            select(FeatureVector)
            .where(
                FeatureVector.symbol == symbol,
                FeatureVector.horizon == "short_term"
            )
            .order_by(FeatureVector.date.asc())
        ).all()

        if len(fvs) < 100:
            raise ValueError(f"Insufficient historical short-term features for {symbol}: {len(fvs)} (need 100+)")

        # 2. Extract features and dates
        data = []
        for fv in fvs:
            # Flatten features into columns
            row = fv.features.copy()
            row["date"] = fv.date
            data.append(row)

        features_df = pd.DataFrame(data).set_index("date")
        features_df.index = pd.to_datetime(features_df.index)
        
        # Ensure unique index just in case
        features_df = features_df[~features_df.index.duplicated(keep="last")]
        features_df.index = pd.to_datetime(features_df.index)

        # 3. Labeling: Find price after `horizon_days`
        # Fetch prices for target calculation
        start_date = features_df.index.min().date()
        end_date = (features_df.index.max() + timedelta(days=horizon_days + 10)).date()

        prices = db.exec(
            select(StockPrice)
            .where(StockPrice.symbol == symbol, StockPrice.date >= start_date, StockPrice.date <= end_date)
            .order_by(StockPrice.date.asc())
        ).all()

        price_series = pd.Series({pd.to_datetime(p.date): p.close for p in prices})

    # Find the price 5 trading days ahead (approx)
    # Since dates may not match exactly due to holidays, we use indices
    aligned_data = []
    available_dates = sorted(price_series.index.tolist())
    logger.info(f"Alignment check for {symbol}: Features={len(features_df)}, Prices={len(price_series)}")
    if available_dates:
        logger.info(f"Index types: df.idx={type(features_df.index[0])}, ps.idx={type(available_dates[0])}")
        logger.info(f"First 5 feature dates: {features_df.index[:5].tolist()}")
        logger.info(f"First 5 price dates: {available_dates[:5]}")

    for i, d in enumerate(features_df.index):
        if i < 5:
            logger.info(f"Row {i} date: {d}, type: {type(d)}")
        try:
            # Use pandas get_loc for faster, more robust matching
            curr_idx = price_series.index.get_loc(d)
            if i < 5:
                logger.info(f"Row {i} curr_idx: {curr_idx}, type: {type(curr_idx)}")
            
            target_idx = curr_idx + horizon_days
            
            if target_idx < len(available_dates):
                curr_price = price_series.iloc[curr_idx] # Safer iloc
                target_price = price_series.iloc[target_idx]
                change_pct = ((target_price - curr_price) / curr_price) * 100
                
                # Labels: 2 = BUY (+2% up), 1 = HOLD (-2 to 2%), 0 = AVOID (<-2% down)
                label = 1
                if change_pct > 2.0: label = 2
                elif change_pct < -2.0: label = 0
                
                row = features_df.loc[d].to_dict()
                row["target_label"] = label
                row["price_change_pct"] = change_pct
                aligned_data.append(row)
        except (ValueError, IndexError):
            continue

    if len(aligned_data) < 50:
        raise ValueError(f"Insufficient aligned training samples for {symbol}: {len(aligned_data)}")

    df = pd.DataFrame(aligned_data)
    
    if df.empty:
        raise ValueError(f"No aligned data samples created for {symbol}. Date mismatch between features and prices?")

    # Prune rows with None values (sometimes indicators fail)
    # df.dropna(inplace=True) 
    
    # Better: identify features with too many NaNs and fill the rest
    nan_counts = df.isnull().sum()
    for col, count in nan_counts.items():
        if count > 0:
            logger.debug(f"Feature '{col}' has {count} missing values in training set.")
            
    df.fillna(0, inplace=True)
    
    X = df.drop(columns=["target_label", "price_change_pct"])
    y = df["target_label"]

    # --- Chronological Split (No leakage) ---
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    logger.info(f"Training XGBoost for {symbol}: Samples={len(X)}, Features={len(X.columns)}")

    # 4. Train Classifier
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        objective="multi:softprob",
        num_class=3,
        random_state=42
    )
    model.fit(X_train, y_train)

    # 5. Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    # Feature Importance
    importance = {k: float(v) for k, v in zip(X.columns, model.feature_importances_)}
    top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10]

    metrics = {
        "accuracy": round(accuracy, 4),
        "train_size": len(X_train),
        "test_size": len(X_test),
        "top_features": importance,
        "symbol": symbol,
        "horizon": f"{horizon_days}d"
    }

    logger.info(f"XGBoost finished for {symbol}: Accuracy={accuracy:.4f}")
    
    return model, metrics
