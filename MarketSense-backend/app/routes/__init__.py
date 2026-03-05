from app.routes import (data_routes, evaluate, fetch_data_route,
                        model_routes, prediction_routes, train_routes)
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(model_routes.router, prefix="/models", tags=["Models"])
api_router.include_router(
    fetch_data_route.router, prefix="/fetch-data", tags=["Fetch Data"]
)
api_router.include_router(data_routes.router, prefix="/data", tags=["Data Ingestion"])
api_router.include_router(train_routes.router, prefix="/train", tags=["Training"])
api_router.include_router(
    prediction_routes.predict_router, prefix="/predict", tags=["Prediction"]
)
api_router.include_router(evaluate.router, prefix="/evaluate", tags=["Evaluation"])
