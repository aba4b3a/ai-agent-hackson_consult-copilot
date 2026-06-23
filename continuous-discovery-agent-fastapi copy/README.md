# Continuous Discovery Agent FastAPI Backend

FastAPI backend for collecting quantitative and qualitative survey data from SMEs, extracting tacit knowledge, storing graph-ready data in BigQuery, and hosting LLM Wiki files on Cloud Storage.

## Architecture

```text
app/
├── api/          # HTTP API only
├── core/         # settings
├── crud/         # DB/storage access only
├── db/           # clients
├── schemas/      # Pydantic DTOs
├── services/     # business logic
└── utils/        # helpers
```

Dependency direction: `api -> services -> crud -> db`.

## Setup

```bash
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs`.

## Main endpoints

- `GET /api/v1/health`
- `POST /api/v1/companies/{company_id}/onboarding/prepare`
- `GET /api/v1/companies/{company_id}/survey/initial`
- `POST /api/v1/companies/{company_id}/survey-responses`
- `GET /api/v1/companies/{company_id}/bigquery/core-tables/ddl`
- `POST /api/v1/companies/{company_id}/bigquery/core-tables`
- `GET /api/v1/companies/{company_id}/graph/query`
- `POST /api/v1/companies/{company_id}/custom-tables/propose`
- `POST /api/v1/companies/{company_id}/wiki/upload`

`DRY_RUN=true` returns planned BigQuery/Storage operations without writing.
