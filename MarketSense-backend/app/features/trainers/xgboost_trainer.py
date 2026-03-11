import logging
from datetime import timedelta
from typing import Dict, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sqlmodel import Session, select

from app.models.feature_data import FeatureVector
from app.models.stock_data import StockPrice

logger = logging.getLogger(__name__)


def train_xgboost_model(
    symbol: str,
    horizon_days: int = 5,
    existing_model_path: Optional[str] = None,
) -> Tuple[xgb.XGBClassifier, Dict]:
    """Train (or warm-start update) an XGBoost classifier for *symbol*.

    When *existing_model_path* is provided the existing booster is loaded and
    used as the starting point via XGBoost's native ``xgb_model`` param in
    ``fit()``.  This appends new trees on top of the existing ones rather than
    training from scratch, preserving learned patterns.

    Args:
        symbol: Stock ticker (e.g. ``RELIANCE.NS``).
        horizon_days: Prediction horizon in trading days.
        existing_model_path: Path to the current active ``.pkl`` bundle.
            If provided, warm-start training is used.

    Returns:
        (model, metrics) — updated classifier + evaluation dict.
    """
    from app.database import engine

    # ── Load existing booster (warm-start) ───────────────────────────────────
    existing_booster: Optional[xgb.XGBClassifier] = None
    existing_last_date: Optional[pd.Timestamp] = None

    if existing_model_path:
        try:
            bundle = joblib.load(existing_model_path)
            if isinstance(bundle, dict):
                existing_booster = bundle.get("model")
                old_metrics = bundle.get("metrics", {})
            else:
                existing_booster = bundle
                old_metrics = {}
            # Try to recover the last training date from saved metrics
            end_str = old_metrics.get("end_date")
            if end_str:
                existing_last_date = pd.to_datetime(end_str)
            logger.info(
                "Warm-start XGBoost for %s: loaded existing booster (last_date=%s)",
                symbol, existing_last_date,
            )
        except Exception as exc:
            logger.warning(
                "Could not load existing XGBoost model for warm-start: %s — "
                "falling back to full training.", exc,
            )
            existing_booster = None

    with Session(engine) as db:
        # 1. Fetch all feature vectors for short_term horizon
        fvs = db.exec(
            select(FeatureVector)
            .where(
                FeatureVector.symbol == symbol,
                FeatureVector.horizon == "short_term",
            )
            .order_by(FeatureVector.date.asc())
        ).all()

        if len(fvs) < 100:
            raise ValueError(
                f"Insufficient historical short-term features for {symbol}: "
                f"{len(fvs)} (need 100+)"
            )

        # 2. Build features DataFrame
        data = []
        for fv in fvs:
            row = fv.features.copy()
            row["date"] = fv.date
            data.append(row)

        features_df = pd.DataFrame(data).set_index("date")
        features_df.index = pd.to_datetime(features_df.index)
        features_df = features_df[~features_df.index.duplicated(keep="last")]

        # 3. Filter to NEW data only when warm-starting
        if existing_booster is not None and existing_last_date is not None:
            new_features_df = features_df[features_df.index > existing_last_date]
            logger.info(
                "Warm-start: %d new feature rows since %s",
                len(new_features_df), existing_last_date.date(),
            )
            if len(new_features_df) < 10:
                logger.warning(
                    "Only %d new rows since last training — "
                    "warm-start skipped, using full dataset.",
                    len(new_features_df),
                )
                new_features_df = features_df
        else:
            new_features_df = features_df

        # 4. Labeling: price direction after horizon_days
        start_date = features_df.index.min().date()
        end_date = (
            features_df.index.max() + timedelta(days=horizon_days + 10)
        ).date()

        prices = db.exec(
            select(StockPrice)
            .where(
                StockPrice.symbol == symbol,
                StockPrice.date >= start_date,
                StockPrice.date <= end_date,
            )
            .order_by(StockPrice.date.asc())
        ).all()

    price_series = pd.Series(
        {pd.to_datetime(p.date): p.close for p in prices}
    )

    available_dates = sorted(price_series.index.tolist())

    aligned_data = []
    for i, d in enumerate(new_features_df.index):
        try:
            curr_idx = price_series.index.get_loc(d)
            target_idx = curr_idx + horizon_days

            if target_idx < len(available_dates):
                curr_price = price_series.iloc[curr_idx]
                target_price = price_series.iloc[target_idx]
                change_pct = ((target_price - curr_price) / curr_price) * 100

                label = 1
                if change_pct > 2.0:
                    label = 2
                elif change_pct < -2.0:
                    label = 0

                row = new_features_df.loc[d].to_dict()
                row["target_label"] = label
                row["price_change_pct"] = change_pct
                aligned_data.append(row)
        except (ValueError, IndexError):
            continue

    min_samples = 10 if existing_booster is not None else 50
    if len(aligned_data) < min_samples:
        raise ValueError(
            f"Insufficient aligned training samples for {symbol}: "
            f"{len(aligned_data)} (need {min_samples}+)"
        )

    df = pd.DataFrame(aligned_data)
    df.fillna(0, inplace=True)

    X = df.drop(columns=["target_label", "price_change_pct"])
    y = df["target_label"]

    # ── Chronological split for evaluation ──────────────────────────────────
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    logger.info(
        "Training XGBoost for %s: samples=%d, features=%d, warm_start=%s",
        symbol, len(X), len(X.columns), existing_booster is not None,
    )

    # ── Train (warm-start if booster available) ──────────────────────────────
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        objective="multi:softprob",
        num_class=3,
        random_state=42,
    )

    if existing_booster is not None:
        # Warm-start: pass existing booster so new trees build on top
        model.fit(
            X_train, y_train,
            xgb_model=existing_booster,
            eval_set=[(X_test, y_test)],
            verbose=False,
        )
    else:
        model.fit(X_train, y_train)

    # ── Evaluate ─────────────────────────────────────────────────────────────
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    importance = {
        k: float(v)
        for k, v in zip(X.columns, model.feature_importances_)
    }

    # Derive training date range from the full feature set used for labels
    end_date_str = str(new_features_df.index.max().date())
    start_date_str = str(new_features_df.index.min().date())

    metrics = {
        "accuracy": round(accuracy, 4),
        "train_size": len(X_train),
        "test_size": len(X_test),
        "top_features": importance,
        "symbol": symbol,
        "horizon": f"{horizon_days}d",
        "warm_start": existing_booster is not None,
        "start_date": start_date_str,
        "end_date": end_date_str,
    }

    logger.info(
        "XGBoost finished for %s: accuracy=%.4f, warm_start=%s",
        symbol, accuracy, existing_booster is not None,
    )

    return model, metrics
