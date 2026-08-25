run:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

api-logs:
	docker compose logs -f api

test:
	docker compose exec api pytest

coverage:
	docker compose exec api pytest --cov=app --cov-report=term-missing

migration:
	docker compose exec api alembic revision --autogenerate -m "$(m)"

migrate:
	docker compose exec api alembic upgrade head

seed:
	docker compose exec api python scripts/seed.py
