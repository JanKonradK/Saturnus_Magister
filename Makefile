# Saturnus_Magister Makefile

.PHONY: help setup install run test clean lint docker-up docker-down

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Initial setup (OAuth + Config)
	@echo "Starting setup..."
	@python scripts/ticktick_oauth.py
	@python -m src.cli.setup
	@echo "Don't forget to update your .env file!"

install: ## Install dependencies
	pip install -e ".[dev]"

run: ## Run the main application
	python -m src.main

review: ## Run manual review queue
	python -m src.cli.review

simulate: ## Run simulation mode
	PYTHONPATH=. python scripts/simulate_full_run.py

test: ## Run tests
	pytest

lint: ## Run linting
	ruff check src

clean: ## Clean up cache files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-up: ## Start Docker containers
	docker-compose -f docker/docker-compose.yml up -d

docker-down: ## Stop Docker containers
	docker-compose -f docker/docker-compose.yml down
