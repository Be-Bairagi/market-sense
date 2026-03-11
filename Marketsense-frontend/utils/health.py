"""Shared backend health check utility.

Extracted to avoid cross-page imports which would accidentally trigger
top-level Streamlit rendering code in app.py when Dashboard imports it.
"""
import requests

BACKEND_URL = "http://localhost:8000"
HEALTH_ENDPOINT = f"{BACKEND_URL}/health"


def check_backend_health() -> tuple[bool, dict | None]:
    """Silently check if the backend is reachable.

    Returns:
        (healthy: bool, health_data: dict | None)
    """
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        if response.status_code == 200:
            return True, response.json()
        return False, None
    except Exception:
        return False, None
