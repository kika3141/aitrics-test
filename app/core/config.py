from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/vitalrisk"
    api_token: str = "dev-secret-token"
    vital_risk_time_window_hours: int = 24
    log_level: str = "DEBUG"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
