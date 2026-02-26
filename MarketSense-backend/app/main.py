from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_db_and_tables
from app.router import router as appRouter
from app.routes import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # This runs at startup
    create_db_and_tables()
    yield
    # Optional shutdown logic can go here


app = FastAPI(
    title=settings.app_name,
    description="M.Tech Final Year Project - MarketSense: AI-powered Stock Market Prediction",  # noqa: E501
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Restricted to Streamlit frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": f"Welcome to {settings.app_name} 🚀"}


app.include_router(api_router)
appRouter(app.include_router)
