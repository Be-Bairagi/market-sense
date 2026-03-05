import logging
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
from sqlmodel import Session, select

from app.models.feature_data import FeatureVector
from app.models.stock_data import StockPrice
from app.services.technical_indicator_service import TechnicalIndicatorService
from app.services.sentiment_service import SentimentService
from app.services.macro_feature_service import MacroFeatureService
from app.services.market_context_service import MarketContextService

logger = logging.getLogger(__name__)


class FeatureComputationService:
    """
    Orchestrator that assembles a complete feature vector for a stock
    by calling all sub-services (technical, sentiment, macro, market context).
    """

    @staticmethod
    def compute_features(symbol: str, horizon: str = "short_term") -> Optional[Dict]:
        """
        Compute the full feature vector for a symbol on the latest available date.
        Returns the feature dict or None if insufficient data.
        """
        from app.database import engine

        with Session(engine) as db:
            # 1. Load OHLCV data for technical indicators
            price_rows = db.exec(
                select(StockPrice)
                .where(StockPrice.symbol == symbol)
                .order_by(StockPrice.date.desc())
                .limit(300)  # ~1+ year of trading days
            ).all()

        if len(price_rows) < 14:
            logger.warning(f"Insufficient price data for {symbol} ({len(price_rows)} rows)")
            return None

        # Convert to DataFrame (reverse to chronological order)
        price_rows = list(reversed(price_rows))
        df = pd.DataFrame([{
            "Open": p.open,
            "High": p.high,
            "Low": p.low,
            "Close": p.close,
            "Volume": p.volume,
        } for p in price_rows], index=[p.date for p in price_rows])

        latest_date = price_rows[-1].date

        # 2. Compute technical indicators
        tech_features = TechnicalIndicatorService.compute_all(df)

        # 3. Compute sentiment features
        sentiment_features = SentimentService.get_sentiment_summary(symbol)

        # 4. Compute macro features
        macro_features = MacroFeatureService.compute_macro_features()

        # 5. Compute market context
        context_features = MarketContextService.compute_context_features()

        # 6. Assemble full feature vector
        all_features = {}
        all_features.update(tech_features)
        all_features.update({f"sentiment_{k}": v for k, v in sentiment_features.items()})
        all_features.update(macro_features)
        all_features.update(context_features)

        # 7. Validate
        validation_errors = FeatureComputationService._validate(all_features)
        if validation_errors:
            logger.warning(f"Feature validation warnings for {symbol}: {validation_errors}")

        # 8. Store in DB
        with Session(engine) as db:
            # Check for existing record
            existing = db.exec(
                select(FeatureVector).where(
                    FeatureVector.symbol == symbol,
                    FeatureVector.date == latest_date,
                    FeatureVector.horizon == horizon,
                )
            ).first()

            if existing:
                existing.features = all_features
                existing.computed_at = datetime.utcnow()
                db.add(existing)
            else:
                fv = FeatureVector(
                    symbol=symbol,
                    date=latest_date,
                    horizon=horizon,
                    features=all_features,
                    computed_at=datetime.utcnow(),
                )
                db.add(fv)

            db.commit()

        logger.info(f"Computed {len(all_features)} features for {symbol} ({latest_date}, {horizon})")
        return all_features

    @staticmethod
    def backfill_features(symbol: str, horizon: str = "short_term"):
        """
        Compute features for all available dates for a stock.
        Uses a sliding window approach over the stored price data.
        """
        from app.database import engine

        with Session(engine) as db:
            price_rows = db.exec(
                select(StockPrice)
                .where(StockPrice.symbol == symbol)
                .order_by(StockPrice.date.asc())
            ).all()

        if len(price_rows) < 200:
            logger.warning(f"Less than 200 data points for {symbol}, computing only for latest date.")
            FeatureComputationService.compute_features(symbol, horizon)
            return

        # Build full DataFrame
        df = pd.DataFrame([{
            "Open": p.open, "High": p.high, "Low": p.low,
            "Close": p.close, "Volume": p.volume,
        } for p in price_rows], index=[p.date for p in price_rows])

        # Compute features on full dataset (sliding window of 200+ rows)
        # For backfill, we compute for the last N dates where we have enough history
        dates_to_compute = df.index[200:]  # Skip first 200 days (need for EMA200)
        computed_count = 0

        # Get macro and context once (they don't change per-date in backfill)
        macro_features = MacroFeatureService.compute_macro_features()
        context_features = MarketContextService.compute_context_features()
        sentiment_features = SentimentService.get_sentiment_summary(symbol)

        with Session(engine) as db:
            for target_date in dates_to_compute:
                # Slice up to this date
                sub_df = df.loc[:target_date]
                tech_features = TechnicalIndicatorService.compute_all(sub_df)

                all_features = {}
                all_features.update(tech_features)
                all_features.update({f"sentiment_{k}": v for k, v in sentiment_features.items()})
                all_features.update(macro_features)
                all_features.update(context_features)

                # Check for existing
                existing = db.exec(
                    select(FeatureVector).where(
                        FeatureVector.symbol == symbol,
                        FeatureVector.date == target_date,
                        FeatureVector.horizon == horizon,
                    )
                ).first()

                if not existing:
                    fv = FeatureVector(
                        symbol=symbol,
                        date=target_date,
                        horizon=horizon,
                        features=all_features,
                        computed_at=datetime.utcnow(),
                    )
                    db.add(fv)
                    computed_count += 1

                    if computed_count % 50 == 0:
                        db.commit()

            db.commit()

        logger.info(f"Backfilled {computed_count} feature vectors for {symbol}")

    @staticmethod
    def _validate(features: Dict) -> List[str]:
        """Validate a feature vector. Returns list of warning messages."""
        errors = []

        # RSI must be 0-100
        rsi = features.get("rsi_14")
        if rsi is not None and (rsi < 0 or rsi > 100):
            errors.append(f"RSI out of range: {rsi}")

        # Bollinger position should be 0-1 (approximately)
        bb_pos = features.get("bollinger_position")
        if bb_pos is not None and (bb_pos < -0.5 or bb_pos > 1.5):
            errors.append(f"Bollinger position unusual: {bb_pos}")

        # Check for critical NaN features
        critical = ["rsi_14", "macd_line", "ema_9", "atr_14", "current_close"]
        for key in critical:
            if key in features and features[key] is None:
                errors.append(f"Critical feature is None: {key}")

        return errors
