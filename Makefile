COMPOSE_FILE=infra/docker-compose.postgres.yml
POSTGRES_CONTAINER=tgi_postgres
COREPACK_HOME?=$(CURDIR)/.corepack
POSTGRES_DB?=tgi_local
POSTGRES_USER?=tgi_user

-include .env
export

.PHONY: db-up db-down db-logs db-restart db-ps db-shell backend-sync backend-run alembic-upgrade alembic-revision frontend-sync frontend-dev frontend-build frontend-lint

# Database
db-up:
	docker compose -f $(COMPOSE_FILE) up -d

db-down:
	docker compose -f $(COMPOSE_FILE) down

db-logs:
	docker compose -f $(COMPOSE_FILE) logs -f postgres

db-restart:
	docker compose -f $(COMPOSE_FILE) restart postgres

db-ps:
	docker compose -f $(COMPOSE_FILE) ps

db-shell:
	docker exec -it $(POSTGRES_CONTAINER) psql -U $${POSTGRES_USER} -d $${POSTGRES_DB}

# Backend
backend-sync:
	cd backend && uv sync

backend-run:
	cd backend && uv run uvicorn app.main:app --reload


# Alembic
alembic-upgrade:
	cd backend && uv run alembic upgrade head

alembic-revision:
	cd backend && uv run alembic revision --autogenerate -m 'init db schema'


# Frontend
frontend-sync:
	cd frontend && COREPACK_HOME=$(COREPACK_HOME) corepack pnpm install

frontend-dev:
	cd frontend && COREPACK_HOME=$(COREPACK_HOME) corepack pnpm dev

frontend-build:
	cd frontend && COREPACK_HOME=$(COREPACK_HOME) corepack pnpm build

frontend-lint:
	cd frontend && COREPACK_HOME=$(COREPACK_HOME) corepack pnpm lint
