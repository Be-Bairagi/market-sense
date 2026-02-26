from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "MarketSense API"
    database_url: str
    debug: bool = False
    # API Key for authentication - must be set via environment
    api_key: str
    # Rate limiting settings
    rate_limit_data: int = 100  # requests per minute for data endpoints
    rate_limit_predict: int = 10  # requests per minute for prediction endpoints

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
