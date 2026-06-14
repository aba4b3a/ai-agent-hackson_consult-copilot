.PHONY: setup dev lint terraform-check test build clean

setup:
	docker compose build
	docker compose run --rm --no-deps front npm install

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

build:
	docker compose run --rm --no-deps front npm run build
	docker build -t consult-copilot-back:local ./back
	docker build -t consult-copilot-agent:local ./agent

clean:
	docker compose down -v
	rm -rf front/.next front/out front/node_modules
	rm -rf back/.venv agent/.venv
