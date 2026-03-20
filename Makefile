.PHONY: install dev test format lint clean run-api run-worker docker-up docker-down help

help:
	@echo "Meeting Agent - Available Commands"
	@echo "=================================="
	@echo "install      - Install package"
	@echo "dev          - Install with dev dependencies"
	@echo "test         - Run tests"
	@echo "format       - Format code with black"
	@echo "lint         - Lint code with ruff"
	@echo "clean        - Remove build artifacts"
	@echo "run-api      - Start API server"
	@echo "run-worker   - Start Celery worker"
	@echo "docker-up    - Start Docker services"
	@echo "docker-down  - Stop Docker services"

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest -v

test-cov:
	pytest --cov=. --cov-report=html --cov-report=term

format:
	black .

lint:
	ruff check .

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run-api:
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

run-worker:
	celery -A api.tasks worker --loglevel=info

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

setup:
	./scripts/quickstart.sh
