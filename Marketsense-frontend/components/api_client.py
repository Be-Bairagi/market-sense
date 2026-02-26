# components/api_client.py
import requests
from utils.config import BASE_URL


def get_prediction(ticker, period):
    url = f"{BASE_URL}/predict?ticker={ticker}&period={period}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def validate_model(ticker, period):
    url = f"{BASE_URL}/validate?ticker={ticker}&period={period}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
