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
                timeout=600,  # training can take a while
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
            return {"error": "Training timed out (> 10 min). The model may still be training in the background."}
        except Exception as e:
            logger.exception(f"Failed to train '{model_type}' model")
            return {"error": f"Failed to train '{model_type}' model: {str(e)}"}


    @staticmethod
    def get_all_models():
        try:
            response = requests.get(f"{BASE_URL}/models/get-all")
            response.raise_for_status()
            res = response.json()

            if not res:
                st.warning("No trained models found.")
                st.stop()

            df = pd.DataFrame(res)

            # Create display-friendly columns
            df["Model"] = df["model_name"] + "_v" + df["version"].astype(str)
            df["Date Trained"] = pd.to_datetime(df["trained_at"]).dt.date
            df["Period"] = df["training_period"]
            df["Status"] = df["is_active"].apply(
                lambda x: "✅ Active" if x else "⏸️ Inactive"
            )

            # Optional: shorten framework name
            df["Framework"] = df["framework"].str.upper()

            display_df = df[
                ["Model", "Framework", "Date Trained", "Period", "Status"]
            ].sort_values(by=["Model", "Date Trained"], ascending=[True, False])

            active_models = df[df["is_active"]]

            st.success(f"✅ Active Models: {len(active_models)}")

            for _, row in active_models.iterrows():
                st.markdown(
                    f"**{row['model_name']} v{row['version']}** "
                    f"({row['framework']}) — trained on `{row['training_period']}`"
                )
            return display_df
        except Exception as e:
            logger.exception("Failed to get the models")
            return {"error": f"Failed to get the models: {str(e)}"}
