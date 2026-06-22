FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
RUN uv pip install --system . --group dev

COPY app ./app
COPY agents ./agents
COPY tools ./tools
COPY eval ./eval
COPY prompts ./prompts
COPY tests ./tests

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
