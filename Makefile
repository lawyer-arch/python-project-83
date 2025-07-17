dev:
	uv run flask --debug --app page_analyzer:app run

install:
	uv sync

PORT ?= 8000

start:
	gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

format:
	ruff check --fix

lint:
	ruff check

.PHONY: dev install start format lint

build:
	./build.sh
