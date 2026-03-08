import logging

import requests
import utils.helpers as helpers
from utils.config import BASE_URL

logger = logging.getLogger(__name__)

# Default API key for development - should be changed in production
API_KEY = "marketsense-api-key-change-in-production"
HEADERS = {"X-API-Key": API_KEY}


class DashboardService:

    # ── Phase 1: existing ────────────────────────────────────
    @staticmethod
    def fetch_stock_data(ticker: str, period: str, interval: str):
        response = requests.get(
            f"{BASE_URL}/fetch-data",
            params={"ticker": ticker, "period": period, "interval": interval},
            timeout=10,
        )
        response.raise_for_status()
        return response.json() if response.ok else {"error": "Data fetch failed"}

    @staticmethod
    def fetch_predictions(model_type: str, ticker: str, predict_days: int):
        model = helpers.to_snake_case(model_type)
        model_name = f"{ticker}_{model}"
        response = requests.get(
            f"{BASE_URL}/predict",
            params={"model_name": model_name, "n_days": predict_days},
            headers=HEADERS,
            timeout=10,
        )
        response.raise_for_status()
        return response.json() if response.ok else {"error": "Prediction fetch failed"}

    # ── Phase 2: Data pipeline ───────────────────────────────
    @staticmethod
    def fetch_data_status():
        """GET /data/status — data coverage summary."""
        try:
            r = requests.get(f"{BASE_URL}/data/status", timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.exception("Failed to fetch data status")
            return {"error": str(e)}

    @staticmethod
    def fetch_macro_data():
        """GET /data/macro — latest macro indicators."""
        try:
            r = requests.get(f"{BASE_URL}/data/macro", timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.exception("Failed to fetch macro data")
            return {"error": str(e)}

    @staticmethod
    def backfill_data(symbol: str):
        """POST /data/backfill — trigger price backfill."""
        try:
            r = requests.post(
                f"{BASE_URL}/data/backfill",
                params={"symbol": symbol},
                headers=HEADERS,
                timeout=10,
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.exception("Failed to trigger backfill for %s: %s", symbol, e)
            return {"error": str(e)}

    # ── Phase 3: Feature engineering ─────────────────────────
    @staticmethod
    def fetch_feature_status():
        """GET /features/status/summary — feature store coverage."""
        try:
            r = requests.get(f"{BASE_URL}/features/status/summary", timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.exception("Failed to fetch feature status")
            return {"error": str(e)}

    @staticmethod
    def fetch_feature_vector(symbol: str, horizon: str = "short_term"):
        """GET /features/{symbol} — latest feature vector for a stock."""
        try:
            r = requests.get(
                f"{BASE_URL}/features/{symbol}",
                params={"horizon": horizon},
                timeout=10,
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.exception("Failed to fetch features for %s: %s", symbol, e)
            return {"error": str(e)}

    @staticmethod
    def backfill_features(symbol: str, horizon: str = "short_term"):
        """POST /features/backfill — trigger feature backfill."""
        try:
            r = requests.post(
                f"{BASE_URL}/features/backfill",
                params={"symbol": symbol, "horizon": horizon},
                timeout=10,
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.exception("Failed to trigger feature backfill for %s: %s", symbol, e)
            return {"error": str(e)}

    # ── Phase 4: Rich prediction ─────────────────────────────
    @staticmethod
    def fetch_rich_prediction(symbol: str, model_type: str = "xgboost"):
        """GET /predict/rich/{symbol} — full PredictionOutput with drivers."""
        try:
            r = requests.get(
                f"{BASE_URL}/predict/rich/{symbol}",
                params={"model_type": model_type},
                headers=HEADERS,
                timeout=30,
            )
            r.raise_for_status()
            return r.json()
        except requests.exceptions.HTTPError as e:
            detail = ""
            try:
                detail = e.response.json().get("detail", "")
            except Exception:
                pass
            logger.error("Rich prediction failed: %s", detail or e)
            return {"error": detail or str(e)}
        except Exception as e:
            logger.exception("Failed to fetch rich prediction")
            return {"error": str(e)}

    # ── Phase 5: Screener ────────────────────────────────────
    @staticmethod
    def fetch_todays_picks():
        """GET /screener/today — today's top 5 stock picks."""
        try:
            r = requests.get(f"{BASE_URL}/screener/today", timeout=15)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.exception("Failed to fetch today's picks")
            return {"error": str(e)}

    @staticmethod
    def fetch_picks_history(days: int = 7):
        """GET /screener/history — past N days of picks."""
        try:
            r = requests.get(
                f"{BASE_URL}/screener/history",
                params={"days": days},
                timeout=15,
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.exception("Failed to fetch picks history")
            return {"error": str(e)}

    @staticmethod
    def trigger_screener():
        """POST /screener/run — manually trigger screener run."""
        try:
            r = requests.post(
                f"{BASE_URL}/screener/run",
                headers=HEADERS,
                timeout=10,
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.exception("Failed to trigger screener")
            return {"error": str(e)}

    # ── Phase 3: Market Pulse ────────────────────────────────
    @staticmethod
    def fetch_market_pulse():
        """GET /market/pulse — Phase 3 macro snapshot."""
        try:
            r = requests.get(f"{BASE_URL}/market/pulse", timeout=10)
            if r.status_code == 404:
                return {"error": "Backend endpoint /api/v1/market/pulse not found."}
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.exception("Failed to fetch market pulse")
            return {"error": str(e)}
