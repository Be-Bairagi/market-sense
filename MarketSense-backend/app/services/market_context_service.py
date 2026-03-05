import logging
from typing import Dict

import pandas as pd
from sqlmodel import Session, select

from app.models.market_data import InstitutionalActivity
from app.models.stock_data import StockPrice

logger = logging.getLogger(__name__)


class MarketContextService:
    """
    Computes market-wide context features:
    - NIFTY 50 trend direction
    - India VIX level
    - FII/DII net activity
    """

    @staticmethod
    def compute_context_features() -> Dict[str, float]:
        """Compute market context features from stored data."""
        from app.database import engine

        features = {}

        with Session(engine) as db:
            # --- NIFTY 50 Trend (using ^NSEI if available) ---
            nifty_prices = db.exec(
                select(StockPrice)
                .where(StockPrice.symbol == "^NSEI")
                .order_by(StockPrice.date.desc())
                .limit(200)
            ).all()

            if len(nifty_prices) >= 50:
                closes = [p.close for p in reversed(nifty_prices)]
                close_series = pd.Series(closes)
                ema_50 = close_series.ewm(span=50, adjust=False).mean().iloc[-1]
                current = close_series.iloc[-1]
                features["nifty_trend_ema50"] = 1.0 if current > ema_50 else 0.0
                features["nifty_above_ema50_pct"] = round(
                    ((current - ema_50) / ema_50) * 100, 4
                )
            else:
                features["nifty_trend_ema50"] = None
                features["nifty_above_ema50_pct"] = None

            # --- FII/DII Net Activity (last 5 days) ---
            fii_dii = db.exec(
                select(InstitutionalActivity)
                .order_by(InstitutionalActivity.date.desc())
                .limit(5)
            ).all()

            if fii_dii:
                features["fii_net_5d"] = sum(r.fii_net for r in fii_dii)
                features["dii_net_5d"] = sum(r.dii_net for r in fii_dii)
            else:
                features["fii_net_5d"] = None
                features["dii_net_5d"] = None

        return features
