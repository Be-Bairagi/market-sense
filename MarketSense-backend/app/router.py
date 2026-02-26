from app.routes.data_route import data_router
from app.routes.evaluate import router as evaluate_router
from app.routes.models import router as models_router
from app.routes.predict import predict_router


def router(appRouter):
    appRouter(data_router)

    appRouter(predict_router)

    appRouter(models_router)

    appRouter(evaluate_router)
