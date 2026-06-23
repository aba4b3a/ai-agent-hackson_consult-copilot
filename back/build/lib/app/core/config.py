from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'Continuous Discovery Agent API'
    app_env: str = 'local'
    debug: bool = True
    dry_run: bool = True
    project_id: str = ''
    location: str = 'asia-northeast1'
    bq_dataset_prefix: str = 'cda'
    bq_graph_name: str = 'KnowledgeGraph'
    wiki_bucket: str = ''
    model_id: str = 'gemini-3.1-pro'

    def dataset_id(self, company_id: str) -> str:
        safe = company_id.replace('-', '_').replace('.', '_')
        return f'{self.bq_dataset_prefix}_{safe}'


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
