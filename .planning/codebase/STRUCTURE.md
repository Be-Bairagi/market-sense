# Codebase Structure

## Directory Layout
```
/
├── MarketSense-backend/    # FastAPI Backend
│   ├── app/                # Application source
│   │   ├── routes/         # API Endpoints
│   │   ├── services/       # Business logic
│   │   ├── models/         # DB Schemas (SQLModel)
│   │   ├── repositories/   # Data access logic
│   │   └── features/       # ML Predictors/Trainers
│   ├── scripts/            # Database and sync utilities
│   └── tests/              # Pytest suite
├── Marketsense-frontend/   # Streamlit Frontend
│   ├── app.py              # Main entry point
│   ├── pages/              # Streamlit page modules
│   ├── services/           # Backend API clients
│   └── components/         # UI helper components
├── .antigravity/           # Project roadmap and scope
└── .planning/              # Phase plans and codebase docs
```

## Key File Locations
- **Backend Entry:** `MarketSense-backend/app/main.py`
- **Frontend Entry:** `Marketsense-frontend/app.py`
- **Configuration:** `MarketSense-backend/app/config.py` and `.env`
- **Database Config:** `MarketSense-backend/app/database.py`

## Where to Add New Code
- **New API Endpoint:** Add to `MarketSense-backend/app/routes/` and register in `main.py`.
- **New ML Model:** Implement trainer/predictor in `MarketSense-backend/app/features/`.
- **New UI Page:** Add to `Marketsense-frontend/pages/`.
- **New Feature Logic:** Add to `MarketSense-backend/app/services/feature_computation_service.py`.
