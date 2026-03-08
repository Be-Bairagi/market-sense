import logging
import time
from contextlib import asynccontextmanager
from starlette.middleware.base import BaseHTTPMiddleware

import sentry_sdk
import yfinance
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sqlalchemy import text

from app.config import settings
from app.database import create_db_and_tables, engine
from app.limiter import limiter
from app.models import feature_data, market_data, prediction_data, screener_data, stock_data  # Import to register with SQLModel
from app.routes import api_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse


logger = logging.getLogger(__name__)


# Request logging middleware
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses."""

    async def dispatch(self, request: Request, call_next):
        # Start timer for response time
        start_time = time.time()

        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else "unknown",
            },
        )

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log errors with traceback
            logger.exception(
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                },
            )
            raise

        # Calculate response time
        process_time = time.time() - start_time

        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"- Status: {response.status_code} - Time: {process_time:.3f}s",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": process_time,
            },
        )

        # Add custom header with response time
        response.headers["X-Process-Time"] = str(process_time)

        return response


# Initialize Sentry for error tracking
def init_sentry():
    """Initialize Sentry SDK for error tracking."""
    dsn = settings.sentry_dsn if hasattr(settings, "sentry_dsn") else None
    if dsn:
        sentry_sdk.init(
            dsn=dsn,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
            ],
            # Filter out expected HTTP errors
            before_send_filter_event=_filter_sentry_events,
            # Set environment
            environment="development" if settings.debug else "production",
            # Sample rate for transactions (0-1)
            traces_sample_rate=0.1,
        )


def _filter_sentry_events(event: dict, hint: dict) -> dict | None:
    """Filter out expected errors that create noise in Sentry."""
    # Check if this is an exception event
    if "exception" in event:
        exception_values = event.get("exception", {}).get("values", [])
        for exc in exception_values:
            exc_type = exc.get("type", "")
            # Filter out HTTPException types
            if exc_type in ("HTTPException", "RateLimitExceeded"):
                return None
    return event


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
    """
    Handle startup and shutdown events for the FastAPI application.
    """
    logger.info("Starting up MarketSense API...")
    # Initialize Sentry for error tracking
    init_sentry()
    # Initialize database
    create_db_and_tables()
    
    # Start background scheduler
    from app.scheduler import start_scheduler, stop_scheduler
    start_scheduler()
    
    yield
    
    # Clean up and shutdown
    logger.info("Shutting down MarketSense API...")
    stop_scheduler()


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


# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)


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
async def health_check():
    """Enhanced health check with database and external API status."""
    health_status = {
        "status": "healthy",
        "version": "1.0.0",
        "checks": {},
    }
    all_healthy = True

    # Check database connectivity
    db_start = time.time()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_response_time = round((time.time() - db_start) * 1000, 2)
        health_status["checks"]["database"] = {
            "status": "healthy",
            "response_time_ms": db_response_time,
        }
    except Exception as e:
        db_response_time = round((time.time() - db_start) * 1000, 2)
        logger.error(f"Database health check failed: {e}")
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "response_time_ms": db_response_time,
            "error": str(e),
        }
        all_healthy = False

    # Check external API (yfinance) availability
    api_start = time.time()
    try:
        # Test with a simple yfinance lookup
        test_ticker = yfinance.Ticker("AAPL")
        _ = test_ticker.info
        api_response_time = round((time.time() - api_start) * 1000, 2)
        health_status["checks"]["yfinance_api"] = {
            "status": "healthy",
            "response_time_ms": api_response_time,
        }
    except Exception as e:
        api_response_time = round((time.time() - api_start) * 1000, 2)
        logger.warning(f"YFinance API health check warning: {e}")
        health_status["checks"]["yfinance_api"] = {
            "status": "degraded",
            "response_time_ms": api_response_time,
            "error": str(e),
        }
        # Don't mark as unhealthy - external API might be temporarily unavailable
        # but app should still function with cached data

    # Overall status
    if not all_healthy:
        health_status["status"] = "unhealthy"

    return health_status


app.include_router(api_router, prefix="/api/v1")

