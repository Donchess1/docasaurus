build:
	docker compose -f docker-compose.yml build
build-staging:
	docker compose -f docker-compose-staging-original.yml up --build --remove-orphans --scale api=1
build-prod:
	docker compose -f docker-compose-prod.yml up --build --remove-orphans --scale api=1

up:
	docker compose -f docker-compose.yml up --build --remove-orphans --scale api=1
up-staging:
	docker compose -f docker-compose-staging.yml up
up-prod:
	docker compose -f docker-compose-prod.yml up

down:
	docker compose -f docker-compose.yml down
down-staging:
	docker compose -f docker-compose-staging.yml down
down-prod:
	docker compose -f docker-compose-prod.yml down

down_volumes:
	docker compose -f docker-compose.yml down -v
down_volumes-staging:
	docker compose -f docker-compose-staging.yml down -v
down_volumes-prod:
	docker compose -f docker-compose-prod.yml down -v

show_logs:
	docker compose -f docker-compose.yml logs
show_logs-staging:
	docker compose -f docker-compose-staging.yml logs
show_logs-prod:
	docker compose -f docker-compose-prod.yml logs

superuser:
	docker compose -f docker-compose.yml run --rm api python3 manage.py createsuperuser
superuser-staging:
	docker compose -f docker-compose-staging-original.yml run --rm api python3 manage.py createsuperuser
superuser-prod:
	docker compose -f docker-compose-prod.yml run --rm api python3 manage.py createsuperuser

migrate:
	docker compose -f docker-compose.yml run --rm api python3 manage.py migrate
migrate-staging:
	docker compose -f docker-compose-staging-original.yml run --rm api python3 manage.py migrate
migrate-prod:
	docker compose -f docker-compose-prod.yml run --rm api python3 manage.py migrate

makemigrations:
	docker compose -f docker-compose.yml run --rm api python3 manage.py makemigrations
makemigrations-staging:
	docker compose -f docker-compose-staging.yml run --rm api python3 manage.py makemigrations
makemigrations-prod:
	docker compose -f docker-compose-prod.yml run --rm api python3 manage.py makemigrations

createwallets:
	docker compose -f docker-compose.yml run --rm api python3 manage.py create_wallets
createwallets-staging:
	docker compose -f docker-compose-staging-original.yml run --rm api python3 manage.py create_wallets
createwallets-prod:
	docker compose -f docker-compose-prod.yml run --rm api python3 manage.py create_wallets

migratewallets:
	docker compose -f docker-compose.yml run --rm api python3 manage.py migrate_wallets
migratewallets-staging:
	docker compose -f docker-compose-staging-original.yml run --rm api python3 manage.py migrate_wallets
migratewallets-prod:
	docker compose -f docker-compose-prod.yml run --rm api python3 manage.py migrate_wallets

black-check:
	docker compose -f docker-compose.yml exec api black --check --exclude=migrations --exclude=/app/venv --exclude=/app/env --exclude=venv --exclude=env .
black-diff:
	docker compose -f docker-compose.yml exec api black --diff --exclude=migrations --exclude=/app/venv --exclude=/app/env --exclude=venv --exclude=env .
black:
	docker compose -f docker-compose.yml exec api black --exclude=migrations --exclude=__init__.py --exclude=admin.py --exclude=/app/venv --exclude=/app/env --exclude=__init__.py --exclude=venv --exclude=env .

isort-check:
	docker compose -f docker-compose.yml exec api isort . --check-only --skip /app/env --skip migrations --skip /app/venv
isort-diff:
	docker compose -f docker-compose.yml exec api isort . --diff --skip /app/env --skip migrations --skip /app/venv
isort:
	docker compose -f docker-compose.yml exec api isort . --skip /app/env --skip migrations --skip=__init__.py --skip=admin.py --skip /app/venv

test:
	docker compose -f docker-compose.yml exec api pytest --ds=core.settings_test

run-test:
	docker compose -f docker-compose.yml exec api pytest $(TEST_PATH)


format:
	make isort
	make black

# build-api:
# 	docker build -t mybapi:dev -f docker/runner/Dockerfile .

# start-api:
# 	docker run -it --name myb-api --env-file=./.env --network=host mybapi:dev