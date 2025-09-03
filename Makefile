COMPOSE = docker-compose -f docker-compose.yml
.DEFAULT_GOAL := help
help: ## Show available commands
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

up: 
	$(COMPOSE) up

down: 
	$(COMPOSE) down

logs: 
	$(COMPOSE) logs -f

bash: 
	$(COMPOSE) exec flask-app bash

worker-bash: 
	$(COMPOSE) exec worker bash

redis-cli: 
	$(COMPOSE) exec redis redis-cli

build: 
	$(COMPOSE) build
