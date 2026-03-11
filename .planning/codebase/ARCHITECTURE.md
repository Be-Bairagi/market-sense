# Architecture Analysis

## Pattern Overview
**Overall:** Layered Monolith with Separate Frontend and Backend (FastAPI + Streamlit).
**Key Characteristics:**
- **Decoupled Architecture:** Backend handles data ingestion, ML processing, and persistence; Frontend handles user interaction and visualization.
- **Service-Oriented Logic:** Business logic is encapsulated in a dedicated `services/` layer.
- **Feature Store Pattern:** Technical indicators and features are pre-computed and stored for model consumption.

## Layers
**API Layer:**
- Location: `MarketSense-backend/app/routes/`
- Purpose: Exposes RESTful endpoints (versioned under `/api/v1`) for the frontend.
- Key Files: `market_routes.py`, `prediction_routes.py`, `stock_routes.py`.

**Service Layer:**
- Location: `MarketSense-backend/app/services/`
- Purpose: Orchestrates business logic, including technical indicator computation, model prediction, and data ingestion.
- Key Files: `prediction_service.py`, `feature_computation_service.py`, `data_ingestion_service.py`.

**Data Access Layer:**
- Location: `MarketSense-backend/app/repositories/` and `app/models/`
- Purpose: Manages database interactions using SQLModel (SQLAlchemy).
- Key Files: `database.py`, `model_registry_repository.py`.

**ML/Predictor Layer:**
- Location: `MarketSense-backend/app/features/`
- Purpose: Contains model-specific training and prediction implementations (Prophet, XGBoost).

## Data Flow
1. **Ingestion:** Data is fetched from `yfinance` or RSS feeds via `fetch_data_service.py`.
2. **Feature Engineering:** `feature_computation_service.py` calculates 40+ technical indicators (RSI, MACD, etc.).
3. **Persistence:** Data is stored in SQLite (dev) or PostgreSQL (prod) via SQLModel.
4. **Prediction:** `prediction_service.py` retrieves features and invokes model predictors to generate BUY/HOLD/AVOID signals.
5. **UI Rendering:** Streamlit frontend calls the backend API and displays interactive Plotly charts.
