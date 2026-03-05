import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from sqlmodel import Session, select
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from app.models.market_data import NewsHeadline

logger = logging.getLogger(__name__)

analyzer = SentimentIntensityAnalyzer()


class SentimentService:
    """
    Scores news headlines using VADER sentiment analysis.
    Updates the `sentiment_score` field on `NewsHeadline` records
    and provides per-stock sentiment summaries.
    """

    @staticmethod
    def score_all_unscored():
        """Score all headlines that don't yet have a sentiment_score."""
        from app.database import engine

        with Session(engine) as db:
            unscored = db.exec(
                select(NewsHeadline).where(NewsHeadline.sentiment_score == None)  # noqa: E711
            ).all()

            scored_count = 0
            for headline in unscored:
                score = analyzer.polarity_scores(headline.headline)
                headline.sentiment_score = score["compound"]  # -1.0 to 1.0
                db.add(headline)
                scored_count += 1

            db.commit()
            logger.info(f"Scored {scored_count} headlines with VADER sentiment.")
            return scored_count

    @staticmethod
    def get_sentiment_summary(symbol: Optional[str] = None) -> Dict[str, float]:
        """
        Get sentiment summary for a stock (or market-wide if symbol is None).
        Returns: { sentiment_24h, sentiment_3d_trend, headline_count }
        """
        from app.database import engine

        now = datetime.utcnow()
        cutoff_24h = now - timedelta(hours=24)
        cutoff_3d = now - timedelta(days=3)

        with Session(engine) as db:
            # 24-hour sentiment
            query_24h = select(NewsHeadline).where(
                NewsHeadline.published_at >= cutoff_24h,
                NewsHeadline.sentiment_score != None,  # noqa: E711
            )
            if symbol:
                query_24h = query_24h.where(NewsHeadline.symbol == symbol)
            headlines_24h = db.exec(query_24h).all()

            # 3-day sentiment
            query_3d = select(NewsHeadline).where(
                NewsHeadline.published_at >= cutoff_3d,
                NewsHeadline.sentiment_score != None,  # noqa: E711
            )
            if symbol:
                query_3d = query_3d.where(NewsHeadline.symbol == symbol)
            headlines_3d = db.exec(query_3d).all()

        avg_24h = 0.0
        if headlines_24h:
            avg_24h = sum(h.sentiment_score for h in headlines_24h) / len(headlines_24h)

        avg_3d = 0.0
        if headlines_3d:
            avg_3d = sum(h.sentiment_score for h in headlines_3d) / len(headlines_3d)

        # Trend: positive means sentiment is improving
        trend = avg_24h - avg_3d

        return {
            "sentiment_24h": round(avg_24h, 4),
            "sentiment_3d_avg": round(avg_3d, 4),
            "sentiment_3d_trend": round(trend, 4),
            "headline_count_24h": len(headlines_24h),
            "headline_count_3d": len(headlines_3d),
        }
