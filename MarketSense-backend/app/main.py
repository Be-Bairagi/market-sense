from contextlib import asynccontextmanager

from app.config import settings
from app.database import create_db_and_tables
from app.limiter import limiter
from app.router import router as appRouter
from app.routes import api_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse


# Rate limit decorators use the limiter from app.limiter module


@limiter.limit("100/minute")
def rate_limit_data(request: Request):
    """Rate limit for data endpoints: 100 requests per minute per IP"""
    pass


@limiter.limit("10/minute")
def rate_limit_predict(request: Request):
    """Rate limit for prediction endpoints: 10 requests per minute per IP"""
    pass


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


# Add rate limiter to app state
app.state.limiter = limiter


# Custom rate limit handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please try again later.",
            "retry_after": exc.detail,
        },
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


# Health check endpoint (no rate limiting, no auth required)
@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0"}


app.include_router(api_router)
appRouter(app.include_router)
