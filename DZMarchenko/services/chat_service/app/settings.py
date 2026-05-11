from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    database_url: str = "sqlite+pysqlite:///:memory:"
    jwt_secret: str = "dev-secret-change-me"
    jwt_alg: str = "HS256"
    notification_service_url: str = "http://localhost:8003"


settings = Settings()

