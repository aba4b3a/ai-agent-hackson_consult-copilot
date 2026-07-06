.PHONY: setup dev lint terraform-check test seed-emulator build clean

setup:
	docker compose build
	# npm install is run during docker compose up in front service

dev:
	docker compose up --build

lint:
	docker compose run --rm --no-deps front npm run lint
	docker compose run --rm --no-deps front npm run typecheck
	docker compose run --rm --no-deps back ruff check .
	docker compose run --rm --no-deps back mypy app
	docker compose run --rm --no-deps agent ruff check .
	docker compose run --rm --no-deps agent mypy .

terraform-check:
	cd infra/terraform && terraform fmt -check -recursive
	cd infra/terraform/environments/dev && terraform init -backend=false
	cd infra/terraform/environments/dev && terraform validate

test:
	docker compose run --rm --no-deps front npm run test:e2e
	docker compose run --rm --no-deps back pytest
	docker compose run --rm --no-deps agent pytest

seed-emulator:
	# The BigQuery emulator has no persistent volume, so its data is lost on
	# every restart; re-run this after that happens.
	docker compose run --rm back python scripts/seed_emulator.py

build:
	docker compose run --rm --no-deps front npm run build
	docker build -t consult-copilot-back:local ./back
	docker build -t consult-copilot-agent:local ./agent

clean:
	docker compose down -v
	rm -rf front/.next front/out front/node_modules
	rm -rf back/.venv agent/.venv
