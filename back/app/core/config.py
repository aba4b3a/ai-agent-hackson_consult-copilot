from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_env: str = "local"
    gcp_project: str = "local-project"
    bigquery_emulator_host: str | None = None
    agent_base_url: str = "http://localhost:8080"


settings = Settings()
