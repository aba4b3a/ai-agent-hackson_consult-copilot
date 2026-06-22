import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    project_id: str = os.getenv("PROJECT_ID", "")
    location: str = os.getenv("LOCATION", "asia-northeast1")
    dry_run: bool = os.getenv("DRY_RUN", "true").lower() == "true"

    bq_dataset_prefix: str = os.getenv("BQ_DATASET_PREFIX", "cda")
    bq_graph_name: str = os.getenv("BQ_GRAPH_NAME", "KnowledgeGraph")

    wiki_bucket: str = os.getenv("WIKI_BUCKET", "")
    model_id: str = os.getenv("MODEL_ID", "gemini-3.1-pro")

    def dataset_id(self, company_id: str) -> str:
        safe_company_id = company_id.replace("-", "_").replace(".", "_")
        return f"{self.bq_dataset_prefix}_{safe_company_id}"


settings = Settings()
