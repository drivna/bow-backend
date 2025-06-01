# Makefile for Flask Docker Application

# Variables
IMAGE_NAME = flask-app
CONTAINER_NAME = flask-app-container
PORT = 4000
COMPOSE_FILE = docker-compose.yml

# Default target
.DEFAULT_GOAL := help

# Help target
.PHONY: help
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Build targets
.PHONY: build
build: ## Build the Docker image using docker-compose
	@echo "Building Docker image with docker-compose..."
	docker-compose -f $(COMPOSE_FILE) build
	@echo "✅ Build completed successfully!"

.PHONY: build-no-cache
build-no-cache: ## Build the Docker image without cache using docker-compose
	@echo "Building Docker image without cache..."
	docker-compose -f $(COMPOSE_FILE) build --no-cache
	@echo "✅ Build completed successfully!"

# Run targets
.PHONY: run
run: ## Start the application in background mode (requires build first)
	@echo "Starting Flask application in background..."
	docker-compose -f $(COMPOSE_FILE) up -d
	@echo "✅ Application started at http://localhost:$(PORT)"
	@echo "Use 'make logs' to view logs or 'make stop' to stop the application"

.PHONY: run-fg
run-fg: ## Start the application in foreground mode (requires build first)
	@echo "Starting Flask application in foreground..."
	docker-compose -f $(COMPOSE_FILE) up
	@echo "✅ Application started at http://localhost:$(PORT)"


.PHONY: down
down: ## Stop and remove containers, networks
	@echo "Stopping and removing containers..."
	docker-compose -f $(COMPOSE_FILE) down
	@echo "✅ Containers stopped and removed"
