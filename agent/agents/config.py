import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# agent/.env を明示的にロード（ADKがどのディレクトリから起動しても動作する）
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(_env_path, override=False)

# Set OLLAMA_API_BASE for LiteLLM if OLLAMA_HOST is specified
_ollama_host = os.getenv("OLLAMA_HOST", "")
if _ollama_host and not os.getenv("OLLAMA_API_BASE"):
    os.environ["OLLAMA_API_BASE"] = _ollama_host


@dataclass(frozen=True)
class Settings:
    project_id: str = os.getenv("PROJECT_ID", os.getenv("GCP_PROJECT", "local-project"))
    location: str = os.getenv("LOCATION", "asia-northeast1")
    dry_run: bool = os.getenv("DRY_RUN", "true").lower() == "true"
    app_env: str = os.getenv("APP_ENV", "local")

    bq_dataset_prefix: str = os.getenv("BQ_DATASET_PREFIX", "cda")
    bq_graph_name: str = os.getenv("BQ_GRAPH_NAME", "KnowledgeGraph")

    wiki_bucket: str = os.getenv("WIKI_BUCKET", "")
    model_id: str = os.getenv("MODEL_ID", "ollama_chat/gemma4:12b")

    # Local development settings
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    bigquery_emulator_host: str = os.getenv("BIGQUERY_EMULATOR_HOST", "")

    def dataset_id(self, company_id: str) -> str:
        safe_company_id = company_id.replace("-", "_").replace(".", "_")
        return f"{self.bq_dataset_prefix}_{safe_company_id}"


settings = Settings()
