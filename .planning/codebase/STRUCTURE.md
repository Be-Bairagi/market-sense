# Codebase Structure

**Analysis Date:** 2026-02-26

## Directory Layout

```
Final Year Project/
├── MarketSense-backend/           # FastAPI backend
│   ├── app/                      # Main application package
│   │   ├── config.py             # Configuration settings
│   │   ├── database.py           # Database connection
│   │   ├── main.py               # FastAPI app entry point
│   │   ├── router.py             # Router aggregator
│   │   ├── models/               # Database models (SQLModel)
│   │   ├── routes/               # API route handlers
│   │   ├── services/             # Business logic
│   │   ├── repositories/         # Data access layer
│   │   ├── schemas/              # Pydantic schemas
│   │   ├── features/             # ML features (trainers, predictors)
│   │   └── utils/                # Utility functions
│   ├── models/                   # Trained model files (.pkl)
│   ├── market_sense.db           # SQLite database
│   └── requirements.txt          # Python dependencies
│
├── Marketsense-frontend/         # Streamlit frontend
│   ├── app.py                    # Streamlit app entry point (home page)
│   ├── pages/                    # Streamlit page modules
│   ├── components/               # Reusable UI components
│   ├── services/                 # API client services
│   ├── utils/                    # Helper functions and config
│   ├── assets/                   # Static assets (images)
│   └── requirements.txt          # Python dependencies
│
└── .planning/                    # Planning artifacts
    └── codebase/                 # Codebase analysis documents
```

## Directory Purposes

**MarketSense-backend/app/:**
- Purpose: Main application package containing all backend code
- Contains: Configuration, database, routing, services, models, schemas
- Key files: `main.py`, `config.py`, `database.py`, `router.py`

**MarketSense-backend/app/routes/:**
- Purpose: API endpoint definitions
- Contains: `models.py`, `predict.py`, `train_routes.py`, `data_route.py`, `evaluate.py`
- Key files: `__init__.py` (aggregates all routers)

**MarketSense-backend/app/services/:**
- Purpose: Business logic implementation
- Contains: `model_service.py`, `prediction_service.py`, `training_service.py`, `prophet_service.py`, `yfinance_data_fetcher.py`

**MarketSense-backend/app/models/:**
- Purpose: SQLModel database schemas
- Contains: `model_registry.py` (TrainedModel table definition)

**MarketSense-backend/app/repositories/:**
- Purpose: Data access abstraction layer
- Contains: `model_registry_repository.py`

**MarketSense-backend/app/features/:**
- Purpose: ML model implementations
- Contains: `trainers/`, `predictors/` subdirectories with Prophet implementations

**MarketSense-backend/app/schemas/:**
- Purpose: Pydantic request/response models
- Contains: `data_fetcher_schemas.py`, `model_registry_schemas.py`

**MarketSense-backend/models/:**
- Purpose: Storage for trained model files
- Contains: `.pkl` files (e.g., `AAPL_prophet_v8.pkl`, `MSFT_prophet_v6.pkl`)

**Marketsense-frontend/pages/:**
- Purpose: Streamlit multi-page application pages
- Contains: `1_Dashboard.py`, `2_Model_Performance.py`, `3_Model_Management.py`, `4_Settings.py`, `5_About.py`
- Naming: Numbered prefix for sidebar ordering

**Marketsense-frontend/services/:**
- Purpose: API client wrappers for backend communication
- Contains: `api_client.py`, `model_service.py`, `dashboard_service.py`

**Marketsense-frontend/components/:**
- Purpose: Reusable UI components
- Contains: `charts.py`, `metrics.py`

**Marketsense-frontend/utils/:**
- Purpose: Configuration and helper functions
- Contains: `config.py`, `helpers.py`

**Marketsense-frontend/assets/:**
- Purpose: Static assets (images, logos)
- Contains: `BrandLogoMarketSense.png`

## Key File Locations

**Entry Points:**
- `MarketSense-backend/app/main.py`: FastAPI application initialization
- `Marketsense-frontend/app.py`: Streamlit home page entry

**Configuration:**
- `MarketSense-backend/app/config.py`: Settings class with Pydantic
- `Marketsense-frontend/utils/config.py`: BASE_URL constant

**Database:**
- `MarketSense-backend/market_sense.db`: SQLite database file
- `MarketSense-backend/app/database.py`: SQLModel engine setup

**Trained Models:**
- `MarketSense-backend/models/*.pkl`: Serialized model files

## Naming Conventions

**Files:**
- Python modules: `snake_case.py` (e.g., `model_service.py`, `data_fetcher.py`)
- Page files: `N_Page_Name.py` with numeric prefix (e.g., `1_Dashboard.py`)

**Directories:**
- All lowercase with underscores: `app/routes/`, `app/services/`

**Classes:**
- PascalCase: `ModelService`, `TrainedModel`, `DashboardService`

**Functions:**
- snake_case: `fetch_stock_data()`, `train_model()`, `get_local_models()`

**Routes/API Endpoints:**
- RESTful: `/models`, `/predict`, `/train`, `/fetch-data`

## Where to Add New Code

**New Backend Feature:**
- API routes: `MarketSense-backend/app/routes/`
- Business logic: `MarketSense-backend/app/services/`
- Database models: `MarketSense-backend/app/models/`
- Tests: Not detected (no test directory)

**New Frontend Feature:**
- Page: `Marketsense-frontend/pages/N_NewFeature.py`
- Service: `Marketsense-frontend/services/new_feature_service.py`
- Component: `Marketsense-frontend/components/new_component.py`

**New ML Model:**
- Trainer: `MarketSense-backend/app/features/trainers/`
- Predictor: `MarketSense-backend/app/features/predictors/`
- Schema: `MarketSense-backend/app/schemas/`

## Special Directories

**MarketSense-backend/models/:**
- Purpose: Stores trained Prophet model pickle files
- Generated: Yes (at runtime when training)
- Committed: No (in .gitignore)

**MarketSense-backend/venv/:**
- Purpose: Python virtual environment
- Generated: Yes (on project setup)
- Committed: No

**Marketsense-frontend/venv_311/:**
- Purpose: Python virtual environment
- Generated: Yes (on project setup)
- Committed: No

---

*Structure analysis: 2026-02-26*
