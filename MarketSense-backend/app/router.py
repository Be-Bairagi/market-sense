from app.routes.evaluate import router as evaluate_router


def router(appRouter):
    appRouter(evaluate_router)
