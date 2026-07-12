# Local Development

This project supports Dev Containers and VS Code Server / Remote SSH with the
host Docker Engine. Docker in Docker is not required.

## Architecture

The project consists of three main components:

- **Front**: Next.js 16 frontend (http://localhost:3000)
- **Back**: FastAPI backend (http://localhost:8000)
- **Agent**: Python AI agent (http://localhost:8080)

Local development uses:
- BigQuery Emulator for database operations
- Ollama for LLM inference

Production deployment uses:
- Google Cloud BigQuery
- Gemini Enterprise API

## Prerequisites

- Docker Engine or Docker Desktop (with Docker Compose v2)
- VS Code connected to this machine by Dev Containers, Remote SSH, or VS Code Server
- 4GB+ RAM for running all services

You do not need to install Node.js, Python, uv, Ollama, or BigQuery Emulator on the host
for the normal compose-based workflow.

## Dev Container

Open `repo-base/` in VS Code and run:

```text
Dev Containers: Reopen in Container
```

The Dev Container uses `docker-outside-of-docker`, so Docker commands inside the
container talk to the host Docker Engine instead of starting a nested Docker
daemon. `LOCAL_WORKSPACE_FOLDER` is passed into the container so compose bind
mounts resolve to host-side paths.

## Start

### Step 1: Setup

Run setup from the repository root:

```bash
make setup
```

This will build all Docker images and install dependencies.

### Step 2: Start Services

```bash
make dev
```

Or run compose directly:

```bash
docker compose --profile dev up --build
```

The following services will start:

- **Frontend**: http://localhost:3000
- **Report screen**: http://localhost:3000/report
- **Backend API**: http://localhost:8000
- **Backend OpenAPI**: http://localhost:8000/docs
- **Backend health**: http://localhost:8000/api/v1/health
- **BigQuery Emulator**: http://localhost:9050
- **Ollama**: http://localhost:11434

### (Optional) Sidecar mode — Cloud Run reproduction

To verify the production Cloud Run sidecar routing locally (nginx +
back + agent on a single host port :8080, sharing localhost like Cloud
Run's multi-container service does):

```bash
make sidecar
# or:
docker compose --profile sidecar up --build
```

Endpoints from the host:

```bash
curl http://localhost:8080/                 # front static (served by nginx)
curl http://localhost:8080/api/v1/health    # back via nginx reverse proxy
curl http://localhost:8080/agent/list-apps  # agent via nginx reverse proxy
```

The dev profile and sidecar profile both bind port 8080; do not run them
at the same time. Switch modes with `docker compose --profile <mode> down`
first, then `up` the other.

### Step 3: Setup Ollama Models

In a new terminal, pull an LLM model:

```bash
docker exec -it ollama-ai ollama pull llama2
```

Available models:
- `llama2` (lightweight, recommended for dev)
- `mistral`
- `neural-chat`
- `dolphin-mixtral`

Model download time: 2-10 minutes depending on model size.

### Step 4: Verify Setup

Check that all services are healthy:

```bash
# Frontend
curl http://localhost:3000

# Backend API
curl http://localhost:8000/api/v1/health

# Expected response
# {"status": "ok", "app": "Continuous Discovery Agent API", "dry_run": true}

# Previous-month report.
# When no saved JSON exists, the backend generates one and stores it under
# tenants/{company_id}/reports/monthly/{YYYY-MM}/report.json.
curl http://localhost:8000/api/v1/companies/SMB-1042/report/monthly

# Ollama
curl http://localhost:11434/api/tags
```

## Common Commands

```bash
make lint
make test
make build
make clean
```

The Makefile runs application checks inside docker compose services, so the host
only needs Docker.

## Development Workflow

### View Logs

```bash
# All services
docker compose --profile dev logs -f

# Specific service
docker compose --profile dev logs -f back
docker compose --profile dev logs -f front
docker compose --profile dev logs -f agent
```

### Restart Services

```bash
# Specific service
docker compose --profile dev up --build back

# All services
docker compose --profile dev up --build
```

### Execute Commands

```bash
# Backend (Python)
docker compose exec back python -m pytest

# Backend (Database)
docker compose exec back python -c "from app.db.bigquery import get_bigquery_client; print(get_bigquery_client())"

# Frontend (Node)
docker compose exec front npm run lint

# Agent
docker compose exec agent python -m pytest
```

### Reset Development Environment

```bash
# Stop all services
docker compose down

# Remove volumes (clears all data)
docker compose down -v

# Start fresh
docker compose --profile dev up --build
```

## Environment Configuration

### Local Environment (.env.local)

```bash
# Location: ./. env.local
APP_ENV=local
GCP_PROJECT=local-project
BIGQUERY_EMULATOR_HOST=http://bigquery-emulator:9050
MODEL_ID=llama2
OLLAMA_HOST=http://ollama:11434
```

### Production Environment

Create `.env.prod` with Google Cloud credentials:

```bash
APP_ENV=production
GCP_PROJECT=<your-gcp-project-id>
MODEL_ID=gemini-3.1-pro
# BigQuery Emulator disabled (uses real BigQuery)
BIGQUERY_EMULATOR_HOST=
```

## Troubleshooting

### Port Already in Use

```bash
# Find process on port
lsof -i :3000

# Kill process
kill -9 <PID>
```

### BigQuery Emulator Connection Refused

```bash
# Verify emulator is running
docker compose ps bigquery-emulator

# Check logs
docker compose logs bigquery-emulator

# Restart
docker compose --profile dev up --build bigquery-emulator
```

### Ollama Connection Issues

```bash
# Verify Ollama is running
docker compose ps ollama

# Check Ollama status
curl http://localhost:11434/api/tags

# Pull a model if none exist
docker exec -it ollama-ai ollama pull llama2
```

### Out of Memory (OOM)

Reduce Ollama memory usage:

```bash
# Edit docker-compose.yaml
# Uncomment deploy section:
# deploy:
#   resources:
#     limits:
#       memory: 4G
```

## API Endpoints

### Health & Status

- `GET /api/v1/health` - Health check

### Companies

- `GET /companies` - List companies
- `POST /companies` - Create company
- `GET /companies/{company_id}` - Get company

### BigQuery Operations

- `GET /companies/{company_id}/bigquery/ddl` - Generate DDL
- `POST /companies/{company_id}/bigquery/execute` - Execute SQL

### Survey

- `POST /companies/{company_id}/survey/response` - Submit survey response

### Knowledge Graph

- `GET /companies/{company_id}/graph/query` - Query knowledge graph

### Wiki

- `GET /companies/{company_id}/wiki` - Get wiki content

### Reports

- `GET /companies/{company_id}/report/monthly` - Load previous-month report from Cloud Storage/local storage, or generate and save it when missing
- `GET /companies/{company_id}/report/weekly` - Legacy weekly report endpoint retained for compatibility

See http://localhost:8000/docs for full API documentation.

## Database Schema

The BigQuery emulator creates the following dataset/tables:

- Dataset: `cda_<company_id>`
- Tables:
  - `survey_responses`
  - `knowledge_nodes`
  - `knowledge_edges`
  - `KnowledgeGraph` (property graph)

## Performance

### Local Development Tips

1. Use lightweight Ollama model (`llama2`) during development
2. Enable caching in Next.js for faster rebuilds
3. Use Docker layer caching for faster rebuilds
4. Monitor Docker memory usage: `docker stats`

### Scaling for Load Testing

1. Increase Docker resource limits in `docker-compose.yaml`
2. Enable auto-scaling in production (Cloud Run)
3. Configure BigQuery slots for higher throughput

## Migration to Production

### Steps

1. Create Google Cloud project
2. Update `.env.prod` with GCP credentials
3. Run `gcloud auth application-default login`
4. Deploy with Terraform: `cd infra && terraform apply`
5. Verify: `curl https://<deployed-url>/api/v1/health`

### Configuration Differences

| Config | Local | Production |
|--------|-------|-----------|
| APP_ENV | local | production |
| MODEL_ID | llama2 | gemini-3.1-pro |
| BigQuery | Emulator | Cloud BigQuery |
| Auth | None | GCP Service Account |
| Compute | Docker Compose | Cloud Run |

## Related Documentation

- [Architecture](./architecture.md)
- [Continuous Discovery Agent Design](./spec/continuous_discovery_agent_design.md)
- [Cost Plan](./cost-plan.md)
- [Security](./security.md)
