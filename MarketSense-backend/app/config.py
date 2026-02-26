from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "MarketSense API"
    database_url: str
    debug: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
