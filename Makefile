.PHONY: build up down restart logs migrate collectstatic deploy env-check status fix-perms

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
	docker compose run --rm --entrypoint python web manage.py collectstatic --noinput

collectstatic: env-check
	docker compose run --rm --entrypoint python web manage.py collectstatic --noinput

fix-perms:
	docker compose run --rm --user root --entrypoint sh web -c 'mkdir -p /app/logs /app/staticfiles && touch /app/logs/kafka.log && chown -R django:django /app/logs /app/staticfiles && chmod 755 /app/logs /app/staticfiles && chmod 664 /app/logs/kafka.log'
deploy: env-check
	docker compose build web
	$(MAKE) fix-perms
	docker compose run --rm --entrypoint python web manage.py migrate --noinput
	docker compose run --rm --entrypoint python web manage.py collectstatic --noinput
	docker compose up -d --force-recreate web

status:
	docker compose ps
