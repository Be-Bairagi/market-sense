# Phase 3 — Feature Engineering Store Workflow

## Prerequisites
- Phase 2 complete (stock prices, macro data, news stored in DB)
- Backend server running (`invoke run` in `MarketSense-backend`)
- Virtual environment activated (`av`)

## Execution Steps

### 1. Install Dependencies
```bash
.\venv\Scripts\python.exe -m pip install ta vaderSentiment
```
> **Note:** `pandas-ta` was originally planned but fails on Python 3.14 due to `numba` build issues. Use `ta` (0.11.0) instead — equivalent indicator coverage, no native compilation.

### 2. Create DB Model
- File: `app/models/feature_data.py`
- Table: `FeatureVector` with JSON `features` column
- Unique constraint on `(symbol, date, horizon)`
- Use `import datetime as dt` pattern to avoid Pydantic type clashing

### 3. Build Services (5 new files)

| Service | File | Responsibility |
|---|---|---|
| TechnicalIndicatorService | `app/services/technical_indicator_service.py` | RSI, MACD, Stochastic, EMAs, ADX, Bollinger, ATR, OBV |
| SentimentService | `app/services/sentiment_service.py` | VADER scoring for `NewsHeadline` records |
| MacroFeatureService | `app/services/macro_feature_service.py` | USD/INR, Crude, VIX levels + daily/5d changes |
| MarketContextService | `app/services/market_context_service.py` | NIFTY 50 trend, FII/DII activity |
| FeatureComputationService | `app/services/feature_computation_service.py` | Orchestrator: assembles + validates + stores |

### 4. Create API Routes
- File: `app/routes/feature_routes.py`
- Endpoints:
  - `POST /features/compute` — compute for a symbol
  - `POST /features/backfill` — backfill historical features
  - `GET /features/{symbol}` — get latest feature vector
  - `GET /features/status/summary` — coverage summary

### 5. Wire Into App
- `app/main.py` → import `feature_data` model
- `app/routes/__init__.py` → register `feature_routes`
- `app/scheduler.py` → add daily feature job at 4:45 PM IST + sentiment scoring after news
- `requirements.txt` → add `ta`, `vaderSentiment`

### 6. Verify
```bash
# Test imports
.\venv\Scripts\python.exe -c "from app.services.feature_computation_service import FeatureComputationService; print('OK')"

# Compute features for one stock
.\venv\Scripts\python.exe -c "
from app.services.feature_computation_service import FeatureComputationService
result = FeatureComputationService.compute_features('RELIANCE.NS')
print(f'Features: {len(result)}')
print(f'Keys: {list(result.keys())[:10]}')
"

# Check DB
.\venv\Scripts\python.exe -c "
import os; from dotenv import load_dotenv; load_dotenv()
from sqlalchemy import create_engine, text
engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as c:
    count = c.execute(text('SELECT COUNT(*) FROM feature_vectors')).scalar()
    print(f'Total feature vectors: {count}')
"
```

## Key Gotchas
1. **`pandas-ta` vs `ta`**: Use `ta` on Python 3.14+ (numba won't compile)
2. **Session management**: All services use `from app.database import engine` + `Session(engine)` internally
3. **Column flattening**: `DataCleanerService` handles yfinance multi-index columns before data reaches indicators
4. **Type sanitization**: All numpy types are cast to native Python floats before DB storage
