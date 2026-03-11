### Testing Strategy (TESTING.md)
The project primarily focuses on backend testing using `pytest`.
- **Framework**: `pytest` with `pytest-asyncio` for asynchronous endpoint testing.
- **Fixtures**: Centralized in `MarketSense-backend/tests/conftest.py`, providing mocked `yfinance` data, sample stock/prediction data, and a `TestClient` for FastAPI.
- **Mocking**: Extensive use of `unittest.mock` to isolate tests from external APIs (like `yfinance` and `prophet`).
- **Organization**: Tests are located in `MarketSense-backend/tests/`, divided into `test_routes/` and `test_services/`.
- **Frontend Testing**: Currently, no dedicated test suite was detected for the Streamlit frontend, suggesting a focus on manual UI verification and backend contract testing.
