.PHONY: setup dev sidecar lint terraform-check test seed-emulator build clean

# The base docker-compose file gates everything by profile now. Every
# command that touches Compose picks a profile — `dev` is the default for
# these targets; use `make sidecar` (or `docker compose --profile sidecar
# ...`) for the Cloud Run reproduction.
COMPOSE := docker compose --profile dev

setup:
	$(COMPOSE) build
	# npm install is run during docker compose up in front service

dev:
	$(COMPOSE) up --build

sidecar:
	docker compose --profile sidecar up --build

lint:
	$(COMPOSE) run --build --rm --no-deps front sh -c "npm ci && npm run lint && npm run typecheck"
	$(COMPOSE) run --build --rm --no-deps back ruff check .
	$(COMPOSE) run --build --rm --no-deps back mypy app
	$(COMPOSE) run --build --rm --no-deps agent ruff check .
	$(COMPOSE) run --build --rm --no-deps agent mypy .

terraform-check:
	cd infra/terraform && terraform fmt -check -recursive
	cd infra/terraform/environments/dev && terraform init -backend=false
	cd infra/terraform/environments/dev && terraform validate

test:
	$(COMPOSE) run --build --rm --no-deps front sh -c "npm ci && npx playwright install chromium && npm run test:e2e"
	$(COMPOSE) run --build --rm --no-deps back pytest
	$(COMPOSE) run --build --rm --no-deps agent pytest

seed-emulator:
	# The BigQuery emulator has no persistent volume, so its data is lost on
	# every restart; re-run this after that happens.
	$(COMPOSE) run --rm back python scripts/seed_emulator.py

build:
	$(COMPOSE) run --rm --no-deps front sh -c "npm ci && npm run build"
	docker build -t consult-copilot-back:local ./back
	docker build -t consult-copilot-agent:local ./agent

clean:
	docker compose --profile dev --profile sidecar down -v
	rm -rf front/.next front/out front/node_modules
	rm -rf back/.venv agent/.venv
