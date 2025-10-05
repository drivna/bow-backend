COMPOSE = docker-compose -f docker-compose.yml
.DEFAULT_GOAL := help

help: ## Show available commands
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build Flask container
	$(COMPOSE) build --no-cache

build-worker: ## Build Celery worker container
	$(COMPOSE) build worker

up-flask: ## Start Flask container
	$(COMPOSE) up  flask-app flask-worker

up-worker: ## Start Celery worker container
	$(COMPOSE) up worker

up: ## Start all containers
	$(COMPOSE) up 

down: ## Stop all containers
	$(COMPOSE) down

logs-flask: ## Tail Flask logs
	$(COMPOSE) logs -f flask-app

logs-worker: ## Tail Celery logs
	$(COMPOSE) logs -f worker

bash-flask: ## Bash into Flask container
	$(COMPOSE) exec flask-app bash

bash-worker: ## Bash into Worker container
	$(COMPOSE) exec worker bash

redis-cli: ## Open Redis CLI
	$(COMPOSE) exec redis redis-cli

psql: ## Open Postgres shell
	docker exec -it postgres-db psql -U postgres bow_db

qdrant: ## Bash into Qdrant
	$(COMPOSE) exec qdrant-db sh
