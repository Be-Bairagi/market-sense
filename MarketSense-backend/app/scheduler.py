import logging
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from app.database import engine
from sqlmodel import Session
from app.services.data_ingestion_service import DataIngestionService
from app.services.feature_computation_service import FeatureComputationService
from app.services.sentiment_service import SentimentService
from app.data.nifty50 import NIFTY_50_STOCKS

logger = logging.getLogger(__name__)

# Indian Standard Time (IST)
IST = pytz.timezone('Asia/Kolkata')

scheduler = BackgroundScheduler(timezone=IST)

def update_nifty50_prices():
    """Daily job to update NIFTY 50 prices."""
    logger.info("Starting scheduled NIFTY 50 price update...")
    for stock in NIFTY_50_STOCKS:
        # For daily updates, we can use a shorter period
        DataIngestionService.backfill_stock(stock["symbol"], years=0) 
    logger.info("Finished scheduled price update.")

def update_market_context():
    """Daily job for macro indicators."""
    logger.info("Starting scheduled macro data update...")
    DataIngestionService.update_macro_data()
    logger.info("Finished scheduled macro update.")

def update_news_headlines():
    """Frequent job for news ingestion."""
    logger.info("Starting scheduled news ingestion...")
    DataIngestionService.fetch_news()
    # Score new headlines immediately after ingestion
    SentimentService.score_all_unscored()
    logger.info("Finished scheduled news ingestion + sentiment scoring.")

def compute_daily_features():
    """Daily job to compute features after price update."""
    logger.info("Starting scheduled feature computation...")
    for stock in NIFTY_50_STOCKS:
        try:
            FeatureComputationService.compute_features(stock["symbol"])
        except Exception as e:
            logger.error(f"Feature computation failed for {stock['symbol']}: {e}")
    logger.info("Finished scheduled feature computation.")

def start_scheduler():
    """Register and start all background jobs."""
    if not scheduler.running:
        # 1. Price updates: Daily at 4:30 PM IST (after market close)
        scheduler.add_job(
            update_nifty50_prices,
            CronTrigger(hour=16, minute=30),
            id="nifty50_update",
            name="Daily NIFTY 50 Price Update",
            replace_existing=True
        )

        # 2. Macro updates: Daily at 7:00 AM IST
        scheduler.add_job(
            update_market_context,
            CronTrigger(hour=7, minute=0),
            id="macro_update",
            name="Daily Macro Data Update",
            replace_existing=True
        )

        # 3. News updates: Every 30 minutes
        scheduler.add_job(
            update_news_headlines,
            IntervalTrigger(minutes=30),
            id="news_update",
            name="Periodic News Ingestion + Sentiment",
            replace_existing=True
        )

        # 4. Feature computation: Daily at 4:45 PM IST (after price update)
        scheduler.add_job(
            compute_daily_features,
            CronTrigger(hour=16, minute=45),
            id="feature_update",
            name="Daily Feature Computation",
            replace_existing=True
        )

        scheduler.start()
        logger.info("Background scheduler started with 4 jobs (IST timezone).")

def stop_scheduler():
    """Shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Background scheduler shut down.")
