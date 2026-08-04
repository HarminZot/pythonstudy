# Развертывание

## Локальная разработка

Проект рассчитан на Python 3.12.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app run.py init-db
flask --app run.py seed-demo
flask --app run.py run
```

## Docker

Перед запуском задайте надежный `SECRET_KEY` в локальном файле `.env`.

```bash
docker compose up --build -d
docker compose exec web flask --app run.py init-db
docker compose exec web flask --app run.py seed-demo
```

## Публичный хостинг

На хостинге задаются переменные `APP_CONFIG=production`, `SECRET_KEY` и `DATABASE_URL`. Команда запуска: `gunicorn --bind 0.0.0.0:$PORT wsgi:app`.
