from app.core.config import settings


def get_agent_base_url() -> str:
    return settings.agent_base_url
