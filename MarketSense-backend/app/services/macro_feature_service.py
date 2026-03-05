import logging
from typing import Dict

import pandas as pd
from sqlmodel import Session, select

from app.models.market_data import MacroData

logger = logging.getLogger(__name__)


class MacroFeatureService:
    """
    Computes macro-economic features from the MacroData table.
    Returns a dict of feature_name -> value.
    """

    @staticmethod
    def compute_macro_features() -> Dict[str, float]:
        """Get the latest macro feature values."""
        from app.database import engine

        features = {}
        indicators = ["USD_INR", "BRENT_CRUDE", "INDIA_VIX"]

        with Session(engine) as db:
            for indicator in indicators:
                rows = db.exec(
                    select(MacroData)
                    .where(MacroData.indicator == indicator)
                    .order_by(MacroData.date.desc())
                    .limit(6)  # Get last 6 entries for change computation
                ).all()

                if not rows:
                    features[f"{indicator.lower()}_level"] = None
                    features[f"{indicator.lower()}_daily_change_pct"] = None
                    features[f"{indicator.lower()}_5d_change_pct"] = None
                    continue

                latest = rows[0].value
                features[f"{indicator.lower()}_level"] = float(latest)

                # Daily change %
                if len(rows) >= 2:
                    prev = rows[1].value
                    if prev > 0:
                        features[f"{indicator.lower()}_daily_change_pct"] = round(
                            ((latest - prev) / prev) * 100, 4
                        )
                    else:
                        features[f"{indicator.lower()}_daily_change_pct"] = 0.0
                else:
                    features[f"{indicator.lower()}_daily_change_pct"] = None

                # 5-day change %
                if len(rows) >= 6:
                    five_days_ago = rows[5].value
                    if five_days_ago > 0:
                        features[f"{indicator.lower()}_5d_change_pct"] = round(
                            ((latest - five_days_ago) / five_days_ago) * 100, 4
                        )
                    else:
                        features[f"{indicator.lower()}_5d_change_pct"] = 0.0
                else:
                    features[f"{indicator.lower()}_5d_change_pct"] = None

        return features
