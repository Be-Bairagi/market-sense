from app.routes.data_route import data_router
from app.routes.evaluate import router as evaluate_router
from app.routes.models import router as models_router
# predict_router removed - now in prediction_routes.py


def router(appRouter):
    appRouter(data_router)

    appRouter(models_router)

    appRouter(evaluate_router)
