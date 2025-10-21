# ============================================================================
# Makefile - Convenience commands
# ============================================================================
.PHONY: install test lint format clean

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test:
	pytest tests/ -v --cov=.

test-quick:
	pytest tests/ -v

lint:
	flake8 .
	pylint data_sources gui library preprocessing recommender utils
	mypy . --ignore-missing-imports

format:
	black .

format-check:
	black --check .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info

run:
	python main.py
