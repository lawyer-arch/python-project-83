# Запуск приложения в режиме разработки
dev:
	uv run flask --debug --app page_analyzer:app run

# Установка зависимостей через
install:
	uv sync

# Настройка порта (по умолчанию 8000)
PORT ?= 8000

# Запуск в продакшен режиме
start:
	gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

# Форматирование кода
format:
	ruff check --fix

# Проверка кода
lint:
	ruff check

.PHONY: dev install start format lint

# Сборка проекта
build:
	./build.sh
