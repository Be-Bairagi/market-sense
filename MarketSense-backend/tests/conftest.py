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
    Sample prediction data for testing (Rich PredictionOutput format).
    """
    return {
        "model": {
            "id": 1,
            "name": "AAPL_prophet",
            "version": 1,
            "framework": "prophet"
        },
        "predictions": {
            "symbol": "AAPL",
            "horizon": "short-term (7d)",
            "direction": "BUY",
            "confidence": 0.85,
            "target_low": 170.5,
            "target_high": 186.0,
            "stop_loss": 165.0,
            "risk_level": "MEDIUM",
            "key_drivers": ["Trend", "Seasonality"],
            "bear_case": "Macro slowdown",
            "predicted_at": "2024-03-15T20:00:00",
            "valid_until": "2024-03-22T20:00:00",
            "model_name": "AAPL_prophet_v1.pkl",
            "model_version": 1
        },
        "metrics": {"MAE": 2.5}
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

    # Use TestClient without rate limiting for tests
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
