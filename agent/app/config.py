from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_env: str = "local"
    # When mock_mode is on, or no Gemini key is configured, extraction falls
    # back to deterministic keyword-based output so local dev and tests run
    # without a real Gemini call.
    mock_mode: bool = True
    gcp_project: str = "local-project"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    # Use the Vertex AI backend (aiplatform.googleapis.com) instead of the
    # Gemini Developer API. Set true when using a Vertex AI API key.
    use_vertexai: bool = False
    gcp_location: str = "global"

    @property
    def use_gemini(self) -> bool:
        return not self.mock_mode and bool(self.gemini_api_key)


settings = Settings()
