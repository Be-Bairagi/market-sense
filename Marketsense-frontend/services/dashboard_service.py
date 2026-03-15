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
    def fetch_predictions(
        model_type: str,
        ticker: str,
        predict_days: int,
        model_name_override: str = None,
    ):
        """Call GET /predict with a specific model name.

        If *model_name_override* is provided it is used directly (e.g.
        ``AAPL_prophet_v12``).  Otherwise the model name is constructed from
        *ticker* + *model_type* as before.
        """
        try:
            if model_name_override:
                model_name = model_name_override
            else:
                model = "xgboost" if "xg" in model_type.lower() else "prophet"
                model_name = f"{ticker}_{model}"
            response = requests.get(
                f"{BASE_URL}/predict",
                params={"model_name": model_name, "n_days": predict_days},
                headers=HEADERS,
                timeout=30,
            )
            response.raise_for_status()
            return response.json() if response.ok else {"error": "Prediction fetch failed"}
        except requests.exceptions.HTTPError as e:
            detail = ""
            try:
                json_resp = e.response.json()
                if isinstance(json_resp, dict):
                    detail = json_resp.get("detail", "")
                else:
                    detail = str(json_resp)
            except Exception:
                pass
            logger.error("Prediction failed: %s", detail or e)
            return {"error": detail or str(e)}
        except Exception as e:
            logger.exception("Failed to fetch predictions")
            return {"error": str(e)}


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

    @staticmethod
    def fetch_ticker_data_status(symbol: str):
        """GET /data/{symbol}/status — specific stock data coverage."""
        try:
            r = requests.get(f"{BASE_URL}/data/{symbol}/status", timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.exception("Failed to fetch data status for %s", symbol)
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

    @staticmethod
    def fetch_ticker_feature_status(symbol: str, horizon: str = "short_term"):
        """GET /features/{symbol}/status — specific stock feature coverage."""
        try:
            r = requests.get(
                f"{BASE_URL}/features/{symbol}/status",
                params={"horizon": horizon},
                timeout=10,
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.exception("Failed to fetch feature status for %s", symbol)
            return {"error": str(e)}

    # ── Phase 3b: Model availability ─────────────────────────
    @staticmethod
    def fetch_available_models(ticker: str):
        """GET /models/available?ticker=... — merged DB + file model list."""
        try:
            r = requests.get(
                f"{BASE_URL}/models/available",
                params={"ticker": ticker},
                timeout=10,
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.exception("Failed to fetch available models for %s", ticker)
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
                json_resp = e.response.json()
                if isinstance(json_resp, dict):
                    detail = json_resp.get("detail", "")
                else:
                    detail = str(json_resp)
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
    # ── Phase 7: Stock Intelligence ──────────────────────────
    @staticmethod
    def fetch_stock_profile(symbol: str):
        """GET /stocks/{symbol}/profile — company meta data."""
        try:
            r = requests.get(
                f"{BASE_URL}/stocks/{symbol}/profile",
                headers=HEADERS,
                timeout=10,
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.exception("Failed to fetch profile for %s", symbol)
            return {"error": str(e)}

    @staticmethod
    def fetch_stock_news(symbol: str, limit: int = 5):
        """GET /stocks/{symbol}/news — rich headlines with sentiment."""
        try:
            r = requests.get(
                f"{BASE_URL}/stocks/{symbol}/news",
                params={"limit": limit},
                headers=HEADERS,
                timeout=10,
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.exception("Failed to fetch news for %s", symbol)
            return {"error": str(e)}

    @staticmethod
    def fetch_stock_accuracy(symbol: str):
        """GET /stocks/{symbol}/accuracy — historical prediction trials."""
        try:
            r = requests.get(
                f"{BASE_URL}/stocks/{symbol}/accuracy",
                headers=HEADERS,
                timeout=10,
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.exception("Failed to fetch accuracy for %s", symbol)
            return {"error": str(e)}

    # ── Phase 7.4: Watchlist ─────────────────────────────────
    @staticmethod
    def fetch_watchlist():
        """GET /watchlist — retrieve enriched watchlist."""
        try:
            r = requests.get(
                f"{BASE_URL}/watchlist",
                headers=HEADERS,
                timeout=15,
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.exception("Failed to fetch watchlist")
            return {"error": str(e)}

    @staticmethod
    def add_to_watchlist(symbol: str, horizon: str = "short_term"):
        """POST /watchlist — add a stock to tracker."""
        try:
            r = requests.post(
                f"{BASE_URL}/watchlist",
                params={"symbol": symbol, "horizon": horizon},
                headers=HEADERS,
                timeout=10,
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.exception("Failed to add %s to watchlist", symbol)
            return {"error": str(e)}

    @staticmethod
    def remove_from_watchlist(symbol: str):
        """DELETE /watchlist/{symbol} — remove a stock from tracker."""
        try:
            r = requests.delete(
                f"{BASE_URL}/watchlist/{symbol}",
                headers=HEADERS,
                timeout=10,
            )
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.exception("Failed to remove %s from watchlist", symbol)
            return {"error": str(e)}
