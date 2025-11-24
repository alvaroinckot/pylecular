.PHONY: help install test test-unit test-integration test-integration-docker clean lint format typecheck

help:
	@echo "Available commands:"
	@echo "  make install              - Install package in development mode"
	@echo "  make test                 - Run all tests"
	@echo "  make test-unit            - Run unit tests only"
	@echo "  make test-integration     - Run integration tests"
	@echo "  make test-integration-docker - Run integration tests with Docker"
	@echo "  make lint                 - Run linting checks"
	@echo "  make format               - Format code"
	@echo "  make typecheck            - Run type checking"
	@echo "  make clean                - Clean up generated files and containers"

install:
	pip install -e .[test]
	cd tests/integration/node_services && npm install

test: test-unit # test-integration

test-unit:
	pytest tests/unit -v

# test-integration:
# 	cd tests/integration && python run_integration_tests.py

# test-integration-docker:
# 	cd tests/integration && python run_integration_tests.py

lint:
	ruff check pylecular tests

format:
	ruff format pylecular tests

typecheck:
	mypy pylecular --ignore-missing-imports

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf build dist .pytest_cache .mypy_cache
	cd tests/integration && docker compose down 2>/dev/null || true
