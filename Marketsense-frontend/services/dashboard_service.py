import requests
import utils.helpers as helpers
from utils.config import BASE_URL

# Default API key for development - should be changed in production
API_KEY = "marketsense-api-key-change-in-production"


class DashboardService:
    @staticmethod
    def fetch_stock_data(ticker: str, period: str, interval: str):
        response = requests.get(
            f"{BASE_URL}/fetch-data",
            params={"ticker": ticker, "period": period, "interval": interval},
        )
        response.raise_for_status()
        return response.json() if response.ok else {"error": "Data fetch failed"}

    @staticmethod
    def fetch_predictions(model_type: str, ticker: str, predict_days: int):
        model = helpers.to_snake_case(model_type)
        model_name = f"{ticker}_{model}"
        response = requests.get(
            f"{BASE_URL}/predict",
            params={
                "model_name": model_name,
                "n_days": predict_days,
            },
            headers={"X-API-Key": API_KEY},
        )
        response.raise_for_status()
        return response.json() if response.ok else {"error": "Prediction fetch failed"}
