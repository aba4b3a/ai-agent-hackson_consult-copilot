FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
RUN uv pip install --system . --group dev

COPY agents ./agents
COPY tools ./tools
COPY eval ./eval
COPY prompts ./prompts
COPY tests ./tests

CMD ["python", "-m", "agents.quality_eval_agent"]
