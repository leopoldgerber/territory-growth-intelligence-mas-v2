COMPOSE_FILE=infra/docker-compose.postgres.yml
REDIS_COMPOSE_FILE=infra/docker-compose.redis.yml
QDRANT_COMPOSE_FILE=infra/docker-compose.qdrant.yml
POSTGRES_CONTAINER=tgi_postgres
COREPACK_HOME?=$(CURDIR)/.corepack
UV_CACHE_DIR?=$(CURDIR)/.uv-cache
POSTGRES_DB?=tgi_local
POSTGRES_USER?=tgi_user

-include .env
export

.PHONY: db-up db-down db-logs db-restart db-ps db-shell redis-up redis-down redis-logs qdrant-up qdrant-down qdrant-logs backend-sync backend-run worker-run worker-run-watch alembic-upgrade alembic-revision frontend-sync frontend-dev frontend-build frontend-lint

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

# Redis
redis-up:
	docker compose -f $(REDIS_COMPOSE_FILE) up -d

redis-down:
	docker compose -f $(REDIS_COMPOSE_FILE) down

redis-logs:
	docker compose -f $(REDIS_COMPOSE_FILE) logs -f redis

# Qdrant
qdrant-up:
	docker compose -f $(QDRANT_COMPOSE_FILE) up -d

qdrant-down:
	docker compose -f $(QDRANT_COMPOSE_FILE) down

qdrant-logs:
	docker compose -f $(QDRANT_COMPOSE_FILE) logs -f qdrant

# Backend
backend-sync:
	cd backend && UV_CACHE_DIR=$(UV_CACHE_DIR) uv sync

backend-run:
	cd backend && uv run uvicorn app.main:app --reload

worker-run:
	cd backend && uv run dramatiq app.ingestion.tasks

worker-run-watch:
	cd backend && uv run watchmedo auto-restart --directory=./app --pattern=*.py --recursive -- uv run dramatiq app.ingestion.tasks


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
