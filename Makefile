.PHONY: build up down restart logs migrate deploy env-check

ENV_FILE=.env

env-check:
	@if [ ! -f $(ENV_FILE) ]; then \
		echo "Ошибка: файл $(ENV_FILE) не найден. Скопируйте .env.example в .env и заполните значения."; \
		exit 1; \
	fi

build: env-check
	docker compose build web

up: env-check
	docker compose up -d

down:
	docker compose down

restart: down up

logs:
	docker compose logs -f web

migrate: env-check
	docker compose exec web python manage.py migrate

deploy: env-check
	docker compose pull db pgadmin kafka
	docker compose build web
	docker compose up -d --force-recreate web
	docker compose exec web python manage.py migrate --noinput

status:
	docker compose ps