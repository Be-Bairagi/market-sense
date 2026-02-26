"""
Tests for data endpoint (GET /data).
"""

import pytest
from unittest.mock import patch
import pandas as pd


@pytest.fixture
def mock_valid_stock_data():
    """Mock stock data for a valid ticker."""
    dates = pd.date_range(start="2024-01-01", end="2024-01-30", freq="D")
    return pd.DataFrame(
        {
            "Date": dates.strftime("%Y-%m-%d"),
            "Open": [150.0 + i * 0.5 for i in range(len(dates))],
            "High": [155.0 + i * 0.5 for i in range(len(dates))],
            "Low": [148.0 + i * 0.5 for i in range(len(dates))],
            "Close": [152.0 + i * 0.5 for i in range(len(dates))],
            "Volume": [1000000 + i * 10000 for i in range(len(dates))],
        }
    )


class TestDataEndpoint:
    """Test cases for GET /data endpoint."""

    def test_valid_ticker_returns_data(self, test_client, mock_valid_stock_data):
        """
        Test that a valid ticker returns 200 with stock data.
        
        Given valid ticker "AAPL"
        When calling GET /data?ticker=AAPL&period=30d&interval=1d
        Then returns 200 with list of daily data
        """
        with patch("app.routes.data_route.fetch_stock_data") as mock_fetch:
            mock_fetch.return_value = mock_valid_stock_data
            
            response = test_client.get("/data?ticker=AAPL&period=30d&interval=1d")
        
        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "AAPL"
        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0

    def test_invalid_ticker_returns_404(self, test_client):
        """
        Test that a valid-format but non-existent ticker returns 404.
        
        Given valid format ticker but no data exists
        When calling GET /data
        Then returns 404 with error message
        """
        with patch("app.routes.data_route.fetch_stock_data") as mock_fetch:
            from fastapi import HTTPException
            mock_fetch.side_effect = HTTPException(
                status_code=404,
                detail="No data found for ticker: XYZ."
            )
            
            response = test_client.get("/data?ticker=XYZ&period=30d&interval=1d")
        
        assert response.status_code == 404

    def test_missing_ticker_returns_422(self, test_client):
        """
        Test that missing ticker parameter returns 422 validation error.
        
        Given no ticker parameter
        When calling GET /data
        Then returns 422 validation error
        """
        response = test_client.get("/data")
        
        assert response.status_code == 422

    def test_invalid_ticker_format_returns_400(self, test_client):
        """
        Test that invalid ticker format returns 400.
        
        Given invalid ticker format (lowercase)
        When calling GET /data
        Then returns 400 with validation error
        """
        response = test_client.get("/data?ticker=aapl")
        
        assert response.status_code == 400

    def test_invalid_period_returns_400(self, test_client):
        """
        Test that invalid period returns 400.
        
        Given invalid period
        When calling GET /data
        Then returns 400 with validation error
        """
        response = test_client.get("/data?ticker=AAPL&period=invalid&interval=1d")
        
        assert response.status_code == 400

    def test_invalid_interval_returns_400(self, test_client):
        """
        Test that invalid interval returns 400.
        
        Given invalid interval
        When calling GET /data
        Then returns 400 with validation error
        """
        response = test_client.get("/data?ticker=AAPL&period=30d&interval=invalid")
        
        assert response.status_code == 400

