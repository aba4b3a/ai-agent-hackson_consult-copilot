from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_env: str = "local"
    mock_mode: bool = True
    gcp_project: str = "local-project"
    gcs_bucket: str = "continuous-discovery-local"
    bigquery_dataset: str = "continuous_discovery"
    elasticsearch_endpoint: str = "http://localhost:9200"
    gemini_model: str = "gemini-2.5-flash"
    bigquery_emulator_host: str | None = None
    agent_base_url: str = "http://localhost:8080"


settings = Settings()
