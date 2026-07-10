FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
RUN uv pip install --system . --group dev

COPY agents ./agents
COPY copilot_agent ./copilot_agent
COPY tools ./tools
COPY eval ./eval
COPY prompts ./prompts
COPY tests ./tests

# /app 直下をエージェントディレクトリとして提供する（apps: agents / copilot_agent）。
# agents = オンボーディング用 Orchestrator、copilot_agent = 会話専用（design §23.6）。
CMD ["adk", "api_server", "--host", "0.0.0.0", "--port", "8080", "."]
