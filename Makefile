COMPOSE ?= docker compose
# Chạy lệnh backend qua `run --rm` để không cần service api đang sống.
BACKEND ?= $(COMPOSE) run --rm api
TEST_DB_URL ?= postgresql+asyncpg://postgres:postgres@postgres:5432/real_estate_test

.PHONY: help up down logs api-logs build ps lint format typecheck test coverage \
        migration migrate downgrade seed reseed create-test-db shell smoke api-test

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-16s %s\n", $$1, $$2}'

up:  ## Dựng toàn bộ stack (postgres, redis, api, frontend, nginx, mailhog)
	$(COMPOSE) up -d --wait postgres redis api
	$(COMPOSE) up -d frontend nginx mailhog

down:  ## Dừng và xóa container
	$(COMPOSE) down

logs:  ## Xem log tất cả service
	$(COMPOSE) logs -f

api-logs:  ## Xem log API
	$(COMPOSE) logs -f api

build:  ## Build lại image backend
	$(COMPOSE) build api

ps:  ## Trạng thái service
	$(COMPOSE) ps

lint:  ## ruff check + ruff format --check
	$(BACKEND) sh -c "ruff check . && ruff format --check ."

format:  ## Tự sửa lint và format
	$(BACKEND) sh -c "ruff check --fix . && ruff format ."

typecheck:  ## mypy
	$(BACKEND) mypy app

create-test-db:  ## Tạo database cho integration test nếu chưa có
	$(COMPOSE) up -d --wait postgres
	$(COMPOSE) exec -T postgres sh -c "psql -U postgres -tc \"SELECT 1 FROM pg_database WHERE datname='real_estate_test'\" | grep -q 1 || psql -U postgres -c 'CREATE DATABASE real_estate_test'"

test: create-test-db  ## Chạy unit + integration test
	$(COMPOSE) run --rm -e TEST_DATABASE_URL=$(TEST_DB_URL) api pytest

coverage: create-test-db  ## Chạy test kèm coverage gate 40%
	$(COMPOSE) run --rm -e TEST_DATABASE_URL=$(TEST_DB_URL) api \
		pytest --cov=app --cov-report=term-missing --cov-fail-under=40

api-test:  ## Chạy Postman collection qua Nginx, lưu báo cáo vào postman/reports/
	./postman/run.sh

migration:  ## Sinh migration mới: make migration m="mô tả"
	$(BACKEND) python -m alembic revision --autogenerate -m "$(m)"

migrate:  ## Áp migration lên head
	$(BACKEND) python -m alembic upgrade head

downgrade:  ## Hạ một bước migration
	$(BACKEND) python -m alembic downgrade -1

seed:  ## Seed dữ liệu mẫu (bỏ qua nếu đã seed)
	$(BACKEND) python scripts/seed.py

reseed:  ## Xóa dữ liệu nghiệp vụ rồi seed lại
	$(BACKEND) python scripts/seed.py --reset

shell:  ## Vào shell trong container backend
	$(BACKEND) bash

smoke: up  ## Kiểm tra nhanh API qua Nginx
	curl -fsS http://localhost:$${HTTP_PORT:-8080}/health && echo "" && echo "OK"
