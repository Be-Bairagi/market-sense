# MarketSense Backend

## Activate Venv

    source venv/Scripts/activate : to activate the virtual env (git-bash)
    . .\venv\Scripts\Activate.ps1 : to activate the virtual env (powershell)
    
# Invoke Commands

    Invoke run : to run the app
    Invoke format: to formats the code

---

## API Authentication

MarketSense API uses API key-based authentication to protect sensitive endpoints.

### Obtaining an API Key

1. The default API key is set in the `.env` file as `API_KEY`
2. For production, generate a strong unique key and update the `.env` file:
   ```
   API_KEY=your-secure-api-key-here
   ```

### Making Authenticated Requests

Include your API key in the `X-API-Key` header for all protected endpoints:

```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/predict?model_name=AAPL_prophet&n_days=30"
```

### Protected Endpoints

The following endpoints require authentication:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/predict` | GET | Get stock predictions |
| `/train` | POST | Train a new model |
| `/models/register` | POST | Register a trained model |

### Public Endpoints

The following endpoints do NOT require authentication:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root endpoint |
| `/health` | GET | Health check |
| `/fetch-data` | GET | Fetch stock data |
| `/models/list` | GET | List available models |
| `/models/predict` | GET | Model prediction |
| `/models/get-all` | GET | Get all registered models |

---

## Rate Limiting

To prevent abuse, the API implements rate limiting:

| Endpoint Type | Limit |
|--------------|-------|
| Data endpoints (`/fetch-data`) | 100 requests/minute |
| Prediction endpoints (`/predict`) | 10 requests/minute |

When rate limit is exceeded, the API returns:
- **Status Code:** 429 Too Many Requests
- **Headers:** `Retry-After` header with seconds to wait

### Rate Limit Headers

All responses include rate limit information:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Unix timestamp when the limit resets
