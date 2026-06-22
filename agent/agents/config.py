import os
from dataclasses import dataclass
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

@dataclass
class AppConfig:
    env: str
    gcp_project_id: str
    gcp_location: str
    local_model_id: str
    prod_model_id: str
    ollama_api_base: str

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def current_model_id(self) -> str:
        return self.prod_model_id if self.is_production else self.local_model_id

    @property
    def current_api_base(self) -> str | None:
        return None if self.is_production else self.ollama_api_base

def get_config() -> AppConfig:
    """環境変数から設定クラスを生成するファクトリ関数"""
    return AppConfig(
        env=os.getenv("APP_ENV", "local"),
        gcp_project_id=os.getenv("GCP_PROJECT_ID", ""),
        gcp_location=os.getenv("GCP_LOCATION", "us-central1"),
        local_model_id=os.getenv("LOCAL_MODEL_ID", "ollama/gemma4:12b"),
        prod_model_id=os.getenv("PROD_MODEL_ID", "vertex_ai/gemini-3.1-pro"),
        ollama_api_base=os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
    )