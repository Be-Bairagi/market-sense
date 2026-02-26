"""
Tests for prediction endpoint (GET /predict).
"""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd


class TestPredictionEndpoint:
    """Test cases for GET /predict endpoint."""

    def test_valid_prediction_request(self, test_client, auth_headers, sample_prediction_data):
        """
        Test that a valid prediction request returns predictions.
        
        Given valid model_name and n_days
        When calling GET /predict?model_name=AAPL_prophet&n_days=7
        Then returns 200 with predictions array
        """
        with patch("app.routes.prediction_routes.PredictionService.predict") as mock_predict:
            mock_predict.return_value = sample_prediction_data
            
            response = test_client.get(
                "/predict?model_name=AAPL_prophet&n_days=7",
                headers=auth_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert isinstance(data["predictions"], list)
        assert len(data["predictions"]) > 0

    def test_invalid_n_days_returns_400(self, test_client, auth_headers):
        """
        Test that invalid n_days returns 400.
        
        Given n_days=0 or negative
        When calling prediction returns 400 with endpoint
        Then validation error
        """
        response = test_client.get(
            "/predict?model_name=AAPL_prophet&n_days=0",
            headers=auth_headers
        )
        
        assert response.status_code == 422  # FastAPI validation error for gt=0

    def test_negative_n_days_returns_422(self, test_client, auth_headers):
        """
        Test that negative n_days returns 422.
        
        Given negative n_days
        When calling prediction endpoint
        Then returns 422 validation error
        """
        response = test_client.get(
            "/predict?model_name=AAPL_prophet&n_days=-5",
            headers=auth_headers
        )
        
        assert response.status_code == 422

    def test_n_days_exceeds_limit_returns_422(self, test_client, auth_headers):
        """
        Test that n_days > 365 returns 422.
        
        Given n_days > 365
        When calling prediction endpoint
        Then returns 422 validation error
        """
        response = test_client.get(
            "/predict?model_name=AAPL_prophet&n_days=400",
            headers=auth_headers
        )
        
        assert response.status_code == 422

    def test_unauthenticated_returns_401(self, test_client):
        """
        Test that unauthenticated request returns 401.
        
        Given no API key
        When calling prediction endpoint
        Then returns 401 Unauthorized
        """
        response = test_client.get("/predict?model_name=AAPL_prophet&n_days=7")
        
        assert response.status_code == 401

    def test_invalid_model_name_format_returns_400(self, test_client, auth_headers):
        """
        Test that invalid model_name format returns 400.
        
        Given invalid model_name format
        When calling prediction endpoint
        Then returns 400 with validation error
        """
        response = test_client.get(
            "/predict?model_name=invalid&n_days=7",
            headers=auth_headers
        )
        
        assert response.status_code == 400

    def test_missing_model_name_returns_422(self, test_client, auth_headers):
        """
        Test that missing model_name returns 422.
        
        Given no model_name parameter
        When calling prediction endpoint
        Then returns 422 validation error
        """
        response = test_client.get(
            "/predict?n_days=7",
            headers=auth_headers
        )
        
        assert response.status_code == 422

    def test_missing_n_days_returns_422(self, test_client, auth_headers):
        """
        Test that missing n_days returns 422.
        
        Given no n_days parameter
        When calling prediction endpoint
        Then returns 422 validation error
        """
        response = test_client.get(
            "/predict?model_name=AAPL_prophet",
            headers=auth_headers
        )
        
        assert response.status_code == 422
