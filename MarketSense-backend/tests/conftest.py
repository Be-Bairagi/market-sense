"""
Pytest configuration and fixtures for MarketSense backend tests.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import pandas as pd

import pytest

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))


@pytest.fixture
def mock_yfinance_data():
    """
    Mock yfinance data for testing.
    Returns a sample DataFrame similar to what yfinance returns.
    """
    dates = pd.date_range(start="2024-01-01", end="2024-01-30", freq="D")
    data = {
        "Open": [150.0 + i * 0.5 for i in range(len(dates))],
        "High": [155.0 + i * 0.5 for i in range(len(dates))],
        "Low": [148.0 + i * 0.5 for i in range(len(dates))],
        "Close": [152.0 + i * 0.5 for i in range(len(dates))],
        "Volume": [1000000 + i * 10000 for i in range(len(dates))],
        "Adj Close": [152.0 + i * 0.5 for i in range(len(dates))],
    }
    return pd.DataFrame(data, index=dates)


@pytest.fixture
def mock_yfinance_download():
    """
    Mock function for yfinance.download to return sample stock data.
    """
    def _mock_download(*args, **kwargs):
        dates = pd.date_range(start="2024-01-01", end="2024-01-30", freq="D")
        data = {
            "Open": [150.0 + i * 0.5 for i in range(len(dates))],
            "High": [155.0 + i * 0.5 for i in range(len(dates))],
            "Low": [148.0 + i * 0.5 for i in range(len(dates))],
            "Close": [152.0 + i * 0.5 for i in range(len(dates))],
            "Volume": [1000000 + i * 10000 for i in range(len(dates))],
            "Adj Close": [152.0 + i * 0.5 for i in range(len(dates))],
        }
        df = pd.DataFrame(data, index=dates)
        df.index.name = "Date"
        return df

    return _mock_download


@pytest.fixture
def sample_stock_data():
    """
    Sample stock data for testing prediction endpoints.
    """
    return {
        "symbol": "AAPL",
        "current_price": 175.50,
        "change": 2.35,
        "change_percent": 1.36,
        "volume": 52341234,
        "market_cap": 2750000000000,
        "high_52w": 199.62,
        "low_52w": 124.17,
    }


@pytest.fixture
def sample_prediction_data():
    """
    Sample prediction data for testing.
    """
    return {
        "symbol": "AAPL",
        "predictions": [
            {"date": "2024-02-01", "predicted_price": 178.25, "lower": 170.50, "upper": 186.00},
            {"date": "2024-02-02", "predicted_price": 179.50, "lower": 171.75, "upper": 187.25},
            {"date": "2024-02-03", "predicted_price": 180.75, "lower": 173.00, "upper": 188.50},
        ],
        "model_used": "prophet",
        "forecast_days": 7,
    }


@pytest.fixture
def sample_historical_data():
    """
    Sample historical data for testing.
    """
    dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
    return pd.DataFrame(
        {
            "Open": [150.0 + i for i in range(30)],
            "High": [155.0 + i for i in range(30)],
            "Low": [148.0 + i for i in range(30)],
            "Close": [152.0 + i for i in range(30)],
            "Volume": [1000000 + i * 10000 for i in range(30)],
        },
        index=dates,
    )


@pytest.fixture
def test_client():
    """
    Create a test client for the FastAPI application.
    """
    from fastapi.testclient import TestClient
    from app.main import app

    # Override rate limiting for tests
    with patch("app.limiter.enabled", False):
        with TestClient(app) as client:
            yield client


@pytest.fixture
def auth_headers():
    """
    Return authentication headers for protected endpoints.
    """
    return {"X-API-Key": "marketsense-api-key-change-in-production"}


@pytest.fixture
def mock_prophet_model():
    """
    Mock Prophet model for testing.
    """
    mock_model = MagicMock()
    mock_model.predict.return_value = pd.DataFrame(
        {
            "ds": pd.date_range(start="2024-02-01", periods=7, freq="D"),
            "yhat": [178.0 + i for i in range(7)],
            "yhat_lower": [170.0 + i for i in range(7)],
            "yhat_upper": [186.0 + i for i in range(7)],
        }
    )
    return mock_model
