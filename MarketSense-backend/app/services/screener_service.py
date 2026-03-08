import datetime as dt
import logging
from typing import Dict, List, Optional

from sqlmodel import Session, select

from app.data.nifty50 import NIFTY_50_STOCKS
from app.database import engine
from app.models.screener_data import DailyPick
from app.repositories.model_registry_repository import ModelRegistryRepository
from app.services.feature_computation_service import FeatureComputationService
from app.services.explanation_service import ExplanationService

logger = logging.getLogger(__name__)


class ScreenerService:
    """
    Automated stock screening engine.
    Scores all tracked NIFTY 50 stocks, applies filters,
    ensures sector diversity, and stores top 5 daily picks.
    """

    # ── Scoring weights (adjustable) ──────────────────────────
    WEIGHT_CONFIDENCE = 0.50
    WEIGHT_RISK_RETURN = 0.20
    WEIGHT_MOMENTUM = 0.15
    WEIGHT_SENTIMENT = 0.15

    # ── Filters ───────────────────────────────────────────────
    MIN_CONFIDENCE = 0.65
    MIN_PRICE = 50.0         # Exclude penny stocks < ₹50
    MAX_ATR_PERCENT = 5.0    # Exclude hyper-volatile stocks
    MAX_PER_SECTOR = 2       # Sector diversity cap
    MIN_SECTORS = 3          # Minimum distinct sectors in top 5

    @staticmethod
    def compute_score(symbol: str, db: Session) -> Optional[Dict]:
        """
        Compute a composite score (0.0–1.0) for a single stock.
        Returns None if the stock can't be scored (no model, no features).
        """
        # 1. Check if a trained model exists for this symbol
        safe_symbol = symbol.replace(".", "_")
        model_name = f"{safe_symbol}_xgboost"
        model = ModelRegistryRepository.get_active_model(db, model_name)

        if not model:
            return None  # No trained model — skip

        # 2. Compute latest features
        try:
            features = FeatureComputationService.compute_features(symbol)
            if not features:
                logger.warning(f"Screener: No features for {symbol}")
                return None
        except Exception as e:
            logger.error(f"Screener: Feature computation failed for {symbol}: {e}")
            return None

        # 3. Run prediction
        try:
            from app.features.predictors.xgboost_predictor import predict_xgboost
            prediction = predict_xgboost(model.file_path, n_days=5)
        except Exception as e:
            logger.error(f"Screener: Prediction failed for {symbol}: {e}")
            return None

        confidence = prediction.get("confidence", 0.0)
        direction = prediction.get("direction", "HOLD")

        # 4. Compute sub-scores
        # a) Confidence score (0-1, already normalized)
        confidence_score = confidence

        # b) Risk-adjusted return score
        target_high = prediction.get("target_high", 0)
        stop_loss = prediction.get("stop_loss", 0)
        curr_price = features.get("current_close", 0)
        if curr_price > 0 and stop_loss > 0:
            upside = (target_high - curr_price) / curr_price
            downside = (curr_price - stop_loss) / curr_price
            risk_return = upside / max(downside, 0.01)  # Higher is better
            risk_return_score = min(risk_return / 5.0, 1.0)  # Normalize to 0-1
        else:
            risk_return_score = 0.5

        # c) Momentum score (RSI + EMA alignment)
        rsi = features.get("rsi_14", 50.0) or 50.0
        ema_9 = features.get("ema_9", 0) or 0
        ema_21 = features.get("ema_21", 0) or 0
        ema_50 = features.get("ema_50", 0) or 0

        # RSI: best when emerging from oversold (30-50 range)
        if 30 <= rsi <= 50:
            rsi_score = 0.8
        elif 50 < rsi <= 65:
            rsi_score = 0.6
        elif rsi < 30:
            rsi_score = 0.4  # Too oversold
        else:
            rsi_score = 0.3  # Overbought

        # EMA alignment: bullish if EMA9 > EMA21 > EMA50
        if ema_9 > ema_21 > ema_50 > 0:
            ema_score = 1.0
        elif ema_9 > ema_21 > 0:
            ema_score = 0.7
        else:
            ema_score = 0.3

        momentum_score = (rsi_score + ema_score) / 2.0

        # d) Sentiment score
        sentiment = features.get("sentiment_sentiment_24h", 0) or 0
        fii_net = features.get("fii_net_5d", 0) or 0
        sentiment_score = max(0, min(1, (sentiment + 1) / 2.0))  # Normalize -1..1 to 0..1
        if fii_net > 0:
            sentiment_score = min(1.0, sentiment_score + 0.1)

        # 5. Composite score
        composite = (
            ScreenerService.WEIGHT_CONFIDENCE * confidence_score +
            ScreenerService.WEIGHT_RISK_RETURN * risk_return_score +
            ScreenerService.WEIGHT_MOMENTUM * momentum_score +
            ScreenerService.WEIGHT_SENTIMENT * sentiment_score
        )

        # Look up sector
        sector = "Unknown"
        for stock in NIFTY_50_STOCKS:
            if stock["symbol"] == symbol:
                sector = stock.get("sector", "Unknown")
                break

        return {
            "symbol": symbol,
            "direction": direction,
            "confidence": confidence,
            "composite_score": round(composite, 4),
            "target_low": prediction.get("target_low", 0),
            "target_high": prediction.get("target_high", 0),
            "stop_loss": prediction.get("stop_loss", 0),
            "risk_level": prediction.get("risk_level", "MEDIUM"),
            "key_drivers": prediction.get("key_drivers", []),
            "bear_case": prediction.get("bear_case", ""),
            "sector": sector,
            "features": features,  # Used for filtering, not stored
        }

    @staticmethod
    def apply_filters(scored_stocks: List[Dict]) -> List[Dict]:
        """Apply beginner-safe filters to scored stocks."""
        filtered = []
        for stock in scored_stocks:
            # Skip AVOID signals
            if stock["direction"] == "AVOID":
                logger.debug(f"Screener filter: {stock['symbol']} excluded (AVOID)")
                continue

            # Minimum confidence
            if stock["confidence"] < ScreenerService.MIN_CONFIDENCE:
                logger.debug(f"Screener filter: {stock['symbol']} excluded (conf={stock['confidence']:.2f})")
                continue

            # Price filter (no penny stocks)
            price = stock["features"].get("current_close", 0) or 0
            if price < ScreenerService.MIN_PRICE:
                logger.debug(f"Screener filter: {stock['symbol']} excluded (price=₹{price})")
                continue

            # Volatility filter (ATR as % of price)
            atr = stock["features"].get("atr_14", 0) or 0
            if price > 0 and (atr / price * 100) > ScreenerService.MAX_ATR_PERCENT:
                logger.debug(f"Screener filter: {stock['symbol']} excluded (ATR%={atr/price*100:.1f}%)")
                continue

            filtered.append(stock)

        logger.info(f"Screener: {len(filtered)}/{len(scored_stocks)} stocks passed filters")
        return filtered

    @staticmethod
    def apply_sector_diversification(filtered_stocks: List[Dict], top_n: int = 5) -> List[Dict]:
        """Ensure top picks span at least MIN_SECTORS distinct sectors."""
        if len(filtered_stocks) <= top_n:
            return filtered_stocks

        # Sort by composite score
        sorted_stocks = sorted(filtered_stocks, key=lambda x: x["composite_score"], reverse=True)

        picks = []
        sector_count = {}

        for stock in sorted_stocks:
            sector = stock["sector"]
            count = sector_count.get(sector, 0)

            if count < ScreenerService.MAX_PER_SECTOR:
                picks.append(stock)
                sector_count[sector] = count + 1

            if len(picks) >= top_n:
                break

        # If we still don't have enough, fill from remaining
        if len(picks) < top_n:
            for stock in sorted_stocks:
                if stock not in picks:
                    picks.append(stock)
                if len(picks) >= top_n:
                    break

        return picks

    @staticmethod
    def run_screener(db: Session = None) -> List[Dict]:
        """
        Full screener pipeline:
        1. Score all NIFTY 50 stocks with trained models
        2. Filter → Sort → Diversify → Store top 5
        """
        own_session = db is None
        if own_session:
            db = Session(engine)

        try:
            today = dt.date.today()
            logger.info(f"Screener: Starting daily scan for {today}...")

            # 1. Score all stocks
            scored = []
            for stock in NIFTY_50_STOCKS:
                symbol = stock["symbol"]
                result = ScreenerService.compute_score(symbol, db)
                if result:
                    scored.append(result)
                    logger.info(f"Screener: {symbol} scored {result['composite_score']:.4f} ({result['direction']})")

            logger.info(f"Screener: Scored {len(scored)} stocks total")

            if not scored:
                logger.warning("Screener: No stocks could be scored. Train models first.")
                return []

            # 2. Apply filters
            filtered = ScreenerService.apply_filters(scored)

            # 3. Sort and diversify
            picks = ScreenerService.apply_sector_diversification(filtered)

            # 4. Clear old picks for today and store new ones
            old_picks = db.exec(
                select(DailyPick).where(DailyPick.date == today)
            ).all()
            for old in old_picks:
                db.delete(old)

            for rank, pick in enumerate(picks, 1):
                daily_pick = DailyPick(
                    date=today,
                    rank=rank,
                    symbol=pick["symbol"],
                    direction=pick["direction"],
                    confidence=pick["confidence"],
                    composite_score=pick["composite_score"],
                    target_low=pick["target_low"],
                    target_high=pick["target_high"],
                    stop_loss=pick["stop_loss"],
                    risk_level=pick["risk_level"],
                    key_drivers=pick["key_drivers"],
                    bear_case=pick["bear_case"],
                    sector=pick["sector"],
                )
                db.add(daily_pick)

            db.commit()
            logger.info(f"Screener: Stored {len(picks)} daily picks for {today}")

            # Return picks without internal data
            return [
                {k: v for k, v in p.items() if k != "features"}
                for p in picks
            ]

        except Exception as e:
            logger.error(f"Screener failed: {e}")
            if own_session:
                db.rollback()
            raise
        finally:
            if own_session:
                db.close()
