import logging
import time

import pandas as pd
import requests
import streamlit as st
from utils.config import BASE_URL

logger = logging.getLogger(__name__)

# Default API key for development - should be changed in production
API_KEY = "marketsense-api-key-change-in-production"


class ModelService:
    @staticmethod
    def get_training_status(ticker: str, model_type: str):
        """Get the current training status for a model."""
        try:
            # This would be called to poll for status if we had a status endpoint
            # For now, return status phases that can be used by the UI
            return {
                "status": "idle",
                "phases": [
                    "Fetching historical data",
                    "Preprocessing data",
                    "Training model",
                    "Evaluating metrics",
                    "Saving model artifact",
                    "Complete"
                ]
            }
        except Exception as e:
            logger.exception("Failed to get training status")
            return {"error": f"Failed to get status: {str(e)}"}
    @staticmethod
    def get_model_list():
        try:
            response = requests.get(f"{BASE_URL}/models/list")

            logger.info(f"Response status: {response.status_code}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.exception("Failed to list models")
            return {"error": f"Failed to list models: {str(e)}"}

    @staticmethod
    def train_model(ticker: str, period: str, model_type: str):
        try:
            response = requests.post(
                f"{BASE_URL}/train",
                params={"model": model_type, "ticker": ticker, "period": period},
                headers={"X-API-Key": API_KEY},
                timeout=1800,  # training can take a while (High-Accuracy Ensemble)
            )

            # Always try to parse JSON first — even on 4xx responses the backend
            # returns a structured body (e.g. 400 detail string or 409 no_improvement).
            try:
                body = response.json()
            except Exception:
                body = {"error": f"Non-JSON response (HTTP {response.status_code})"}

            if response.status_code == 200:
                return body

            if response.status_code == 409:
                # Metric guard fired — return the structured body so the UI can
                # show old vs new metrics.
                detail = body.get("detail", body)
                if isinstance(detail, dict):
                    return detail  # {"error": "no_improvement", "old_metrics": ..., "new_metrics": ...}
                return {"error": "no_improvement", "message": str(detail)}

            # 400 or other 4xx/5xx
            detail = body.get("detail", body)
            if isinstance(detail, dict):
                return {"error": detail.get("error", "training_failed"), **detail}
            return {"error": str(detail)}

        except requests.exceptions.Timeout:
            return {"error": "Training is still processing (> 30 min). The High-Accuracy model is training in the background; please check the Model Management page in a few minutes."}
        except Exception as e:
            logger.exception(f"Failed to train '{model_type}' model")
            return {"error": f"Failed to train '{model_type}' model: {str(e)}"}


    @staticmethod
    def delete_model(model_id: int) -> dict:
        """Delete a specific model by ID."""
        try:
            response = requests.delete(
                f"{BASE_URL}/models/{model_id}",
                headers={"X-API-Key": API_KEY},
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.exception("Failed to delete model")
            return {"error": f"Failed to delete model: {str(e)}"}

    @staticmethod
    def delete_all_models() -> dict:
        """Delete all models from the registry."""
        try:
            response = requests.delete(
                f"{BASE_URL}/models/all",
                headers={"X-API-Key": API_KEY},
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.exception("Failed to delete all models")
            return {"error": f"Failed to delete all models: {str(e)}"}

    @staticmethod
    def get_all_models():
        """Fetch all models and return a display-friendly DataFrame."""
        try:
            response = requests.get(f"{BASE_URL}/models/get-all")
            response.raise_for_status()
            res = response.json()

            if not res:
                return pd.DataFrame()

            df = pd.DataFrame(res)

            # Create display-friendly columns
            from utils.helpers import format_date
            from data.nifty50 import NIFTY_50_MAP

            def get_company_info(model_name):
                # Strip the framework suffix to get the safe ticker
                frameworks = ["_xgboost", "_prophet", "_lstm", "_hybrid", "_sklearn", "_keras", "_pytorch"]
                safe_ticker = model_name
                for fw in frameworks:
                    if safe_ticker.endswith(fw):
                        safe_ticker = safe_ticker[:-len(fw)]
                        break
                
                # Reconstruct the original ticker (e.g., RELIANCE_NS -> RELIANCE.NS)
                ticker = safe_ticker.replace("_", ".")
                company = NIFTY_50_MAP.get(ticker, ticker)
                return company, ticker

            # Apply parsing
            info = df["model_name"].apply(get_company_info)
            df["Company"] = [i[0] for i in info]
            df["Ticker"] = [i[1] for i in info]

            df["Model"] = df["model_name"] + "_v" + df["version"].astype(str)
            df["Date Trained"] = df["trained_at"].apply(lambda x: format_date(x))
            df["Period"] = df["training_period"]
            df["Framework"] = df["framework"].str.upper()

            # Include Company and Ticker in the final DataFrame for grouped UI
            display_df = df[
                ["id", "Company", "Ticker", "Model", "Framework", "Date Trained", "Period"]
            ].sort_values(by=["Company", "Model", "Date Trained"], ascending=[True, True, False])

            return display_df
        except Exception as e:
            logger.exception("Failed to get the models from registry")
            return {"error": f"Failed to get models: {str(e)}"}
