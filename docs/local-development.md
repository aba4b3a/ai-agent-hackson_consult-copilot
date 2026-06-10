# Local Development

This project supports Dev Containers and VS Code Server / Remote SSH with the
host Docker Engine. Docker in Docker is not required.

## Prerequisites

- Docker Engine or Docker Desktop
- Docker Compose v2
- VS Code connected to this machine by Dev Containers, Remote SSH, or VS Code Server

You do not need to install Node.js, Python, uv, or BigQuery Emulator on the host
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

Run setup and development services from the repository root:

```bash
make setup
make dev
```

Or run compose directly:

```bash
docker compose up --build
```

Open:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Backend health: http://localhost:8000/healthz
- Backend OpenAPI: http://localhost:8000/docs
- BigQuery Emulator: http://localhost:9050

## Common Commands

```bash
make lint
make test
make build
make clean
```

The Makefile runs application checks inside docker compose services, so the host
only needs Docker.
