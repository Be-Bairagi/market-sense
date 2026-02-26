import requests
from utils.config import BASE_URL


def train_model(ticker: str, period: str):
    response = requests.post(
        f"{BASE_URL}/train", params={"ticker": ticker, "period": period}
    )
    return response.json() if response.ok else {"error": "Training failed"}


def predict_stock(ticker: str, period: str):
    response = requests.get(
        f"{BASE_URL}/predict", params={"ticker": ticker, "period": period}
    )
    return response.json() if response.ok else {"error": "Prediction failed"}


def validate_model(ticker: str, period: str):
    response = requests.get(
        f"{BASE_URL}/validate", params={"ticker": ticker, "period": period}
    )
    return response.json() if response.ok else {"error": "Validation failed"}
