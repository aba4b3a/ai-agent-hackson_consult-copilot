from functools import lru_cache
import os
from typing import Any
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'Continuous Discovery Agent API'
    app_env: str = os.getenv('APP_ENV', 'local')
    debug: bool = os.getenv('APP_ENV', 'local') == 'local'
    dry_run: bool = os.getenv('DRY_RUN', 'true').lower() == 'true'
    project_id: str = os.getenv('GCP_PROJECT', 'local-project')
    location: str = os.getenv('LOCATION', 'asia-northeast1')
    bq_dataset_prefix: str = os.getenv('BQ_DATASET_PREFIX', 'consultant_copilot')
    bq_graph_name: str = os.getenv('BQ_GRAPH_NAME', 'KnowledgeGraph')
    wiki_bucket: str = os.getenv('WIKI_BUCKET', '')
    storage_emulator_root: str = os.getenv('STORAGE_EMULATOR_ROOT', '.local_storage')
    model_id: str = os.getenv('MODEL_ID', 'gemini-3.1-pro')
    ollama_host: str = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
    bigquery_emulator_host: str = os.getenv('BIGQUERY_EMULATOR_HOST', '')
    agent_base_url: str = os.getenv('AGENT_BASE_URL', 'http://localhost:8080')

    @field_validator('debug', mode='before')
    @classmethod
    def parse_debug(cls, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in {'1', 'true', 'yes', 'on', 'debug', 'local'}
        return bool(value)

    def dataset_id(self) -> str:
        """The single shared BigQuery dataset every table lives in. Company-
        specific tables are distinguished by a table-name prefix instead of a
        per-company dataset — see ``company_table``/``qualified_table``."""
        return self.bq_dataset_prefix

    @staticmethod
    def safe_company_id(company_id: str) -> str:
        return company_id.replace('-', '_').replace('.', '_')

    def company_table(self, company_id: str, table: str) -> str:
        return f'{self.safe_company_id(company_id)}_{table}'

    def qualified_table(self, company_id: str, table: str) -> str:
        return f'{self.project_id}.{self.dataset_id()}.{self.company_table(company_id, table)}'

    def qualified_common_table(self, table: str) -> str:
        """For genuinely global tables (company registry, migration
        history, ...) that aren't scoped to one company and so carry no
        table-name prefix."""
        return f'{self.project_id}.{self.dataset_id()}.{table}'


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
