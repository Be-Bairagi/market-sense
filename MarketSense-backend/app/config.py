import logging
import os
from logging.handlers import RotatingFileHandler
from typing import ClassVar

from pydantic_settings import BaseSettings


def setup_logging() -> None:
    """Configure application logging with console and file handlers."""
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Log format with timestamp
    log_format = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (INFO level)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_format)
    root_logger.addHandler(console_handler)

    # File handler with rotation (DEBUG level)
    file_handler = RotatingFileHandler(
        filename=os.path.join(log_dir, "marketsense.log"),
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=5,
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_format)
    root_logger.addHandler(file_handler)

    # Set levels for third-party loggers to reduce noise
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("yfinance").setLevel(logging.WARNING)
    logging.getLogger("prophet").setLevel(logging.WARNING)


class Settings(BaseSettings):
    # Logging levels
    LOG_LEVELS: ClassVar[dict] = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }
    app_name: str = "MarketSense API"
    database_url: str
    debug: bool = False
    # API Key for authentication - must be set via environment variable
    api_key: str = "marketsense-api-key-change-in-production"
    # Rate limiting settings
    rate_limit_data: int = 100  # requests per minute for data endpoints
    rate_limit_predict: int = 10  # requests per minute for prediction endpoints
    # Sentry DSN for error tracking (optional)
    sentry_dsn: str | None = None

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

# Initialize logging after settings are loaded
setup_logging()
