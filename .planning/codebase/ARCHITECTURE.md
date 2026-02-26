# Architecture

**Analysis Date:** 2026-02-26

## Pattern Overview

**Overall:** Layered Architecture with Service-Oriented Design

The MarketSense application follows a layered architecture pattern commonly used in Python web applications. The backend uses FastAPI with clear separation between routes, services, repositories, and models. The frontend uses Streamlit for a data-driven dashboard interface.

**Key Characteristics:**
- **Backend (FastAPI):** Routes → Services → Repositories → Models (Database)
- **Frontend (Streamlit):** Pages → Services → API Client → Backend
- **API Communication:** RESTful HTTP between frontend and backend
- **Data Flow:** Pull-based (frontend calls backend APIs)

## Layers

**Backend (MarketSense-backend/app/):**

**Routes Layer (`app/routes/`):**
- Purpose: Define API endpoints and handle HTTP requests/responses
- Location: `MarketSense-backend/app/routes/`
- Contains: `models.py`, `predict.py`, `train_routes.py`, `data_route.py`, `evaluation_service.py`
- Depends on: Services layer
- Used by: Frontend via HTTP calls

**Services Layer (`app/services/`):**
- Purpose: Business logic implementation
- Location: `MarketSense-backend/app/services/`
- Contains: `model_service.py`, `prediction_service.py`, `training_service.py`, `prophet_service.py`, `yfinance_data_fetcher.py`
- Depends on: Repositories, Models, External APIs (yfinance)
- Used by: Routes layer

**Repositories Layer (`app/repositories/`):**
- Purpose: Data access abstraction
- Location: `MarketSense-backend/app/repositories/`
- Contains: `model_registry_repository.py`
- Depends on: Models (SQLModel/SQLAlchemy)
- Used by: Services layer

**Models Layer (`app/models/`):**
- Purpose: Database schema definitions
- Location: `MarketSense-backend/app/models/`
- Contains: `model_registry.py` (SQLModel for trained models table)
- Depends on: SQLModel
- Used by: Repositories

**Features Layer (`app/features/`):**
- Purpose: ML model implementations (trainers and predictors)
- Location: `MarketSense-backend/app/features/`
- Contains: `trainers/prophet_trainer.py`, `predictors/prophet_predictor.py`
- Depends on: Prophet library
- Used by: Services layer

**Schemas Layer (`app/schemas/`):**
- Purpose: Pydantic request/response models
- Location: `MarketSense-backend/app/schemas/`
- Contains: `data_fetcher_schemas.py`, `model_registry_schemas.py`
- Used by: Routes and Services

**Frontend (Marketsense-frontend/):**

**Pages Layer (`pages/`):**
- Purpose: Streamlit page components (UI)
- Location: `Marketsense-frontend/pages/`
- Contains: `1_Dashboard.py`, `2_Model_Performance.py`, `3_Model_Management.py`, `4_Settings.py`, `5_About.py`
- Depends on: Services, Components
- Used by: Streamlit runtime

**Services Layer (`services/`):**
- Purpose: API client wrappers and business logic
- Location: `Marketsense-frontend/services/`
- Contains: `api_client.py`, `model_service.py`, `dashboard_service.py`
- Depends on: Backend APIs (requests library)
- Used by: Pages

**Components Layer (`components/`):**
- Purpose: Reusable UI components
- Location: `Marketsense-frontend/components/`
- Contains: `charts.py`, `metrics.py`, `api_client.py`
- Used by: Pages

**Utils Layer (`utils/`):**
- Purpose: Helper functions and configuration
- Location: `Marketsense-frontend/utils/`
- Contains: `config.py`, `helpers.py`

## Data Flow

**Training Flow:**
1. User selects ticker, period, and model type in frontend
2. Frontend calls `POST /train` endpoint
3. Route receives request → calls TrainingService
4. TrainingService fetches data from yfinance → trains model
5. Model saved to `MarketSense-backend/models/` directory
6. Model metadata stored in database via ModelRegistryRepository
7. Response returned to frontend

**Prediction Flow:**
1. User requests prediction in Dashboard page
2. Frontend calls `GET /prediction-model/predict` endpoint
3. Route receives request → calls PredictionService
4. PredictionService loads trained model → generates predictions
5. Response with predictions returned to frontend
6. Frontend renders chart using Plotly

## Key Abstractions

**API Router:**
- Purpose: Central API route registration
- Location: `MarketSense-backend/app/routes/__init__.py`
- Pattern: FastAPI APIRouter aggregation

**Model Registry:**
- Purpose: Track trained models and their versions
- Location: `MarketSense-backend/app/models/model_registry.py`
- Pattern: SQLModel ORM with version tracking

**Data Fetcher:**
- Purpose: Abstract stock data retrieval from yfinance
- Location: `MarketSense-backend/app/services/yfinance_data_fetcher.py`
- Pattern: Service with external API integration

## Entry Points

**Backend Entry:**
- Location: `MarketSense-backend/app/main.py`
- Triggers: `uvicorn app.main:app` command
- Responsibilities: FastAPI app initialization, CORS setup, lifespan management, router inclusion

**Frontend Entry:**
- Location: `Marketsense-frontend/app.py`
- Triggers: `streamlit run app.py` command
- Responsibilities: Streamlit page configuration, hero section, feature cards rendering

**Database:**
- Location: `MarketSense-backend/market_sense.db` (SQLite)
- Configured in: `MarketSense-backend/app/database.py`

## Error Handling

**Strategy:** HTTPException-based with fallback error responses

**Patterns:**
- Route-level: `raise HTTPException(status_code=..., detail=...)`
- Service-level: Try/except blocks returning error dictionaries
- Frontend-level: Try/except with `st.error()` display

## Cross-Cutting Concerns

**Logging:** Python logging module used in services (`logging.getLogger(__name__)`)

**Validation:** Pydantic schemas in `app/schemas/` for request validation

**Authentication:** Not implemented (CORS allows all origins)

**Configuration:** Pydantic Settings in `app/config.py` with `.env` support

---

*Architecture analysis: 2026-02-26*
