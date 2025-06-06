# Makefile for mcp-mediawiki Docker operations

# Image name and tag
IMAGE_NAME = mcp-mediawiki
TAG = latest

# Full image reference
IMAGE = $(IMAGE_NAME):$(TAG)

# Default target
.PHONY: all
all: build

# Build the Docker image
.PHONY: build
build:
	@echo "Building Docker image $(IMAGE)..."
	docker build -t $(IMAGE) .
	@echo "Image built successfully!"

# Run the Docker container using docker-compose
.PHONY: up
up:
	docker compose up

# Run the Docker container in detached mode
.PHONY: up-detached
up-detached:
	docker compose up -d

# Run with custom arguments - example: make run-args ARGS="--api-host=mywiki.org --username=bot"
.PHONY: run-args
run-args:
	@if [ -z "$(ARGS)" ]; then \
		echo "Usage: make run-args ARGS=\"--api-host=mywiki.org --username=bot\""; \
		exit 1; \
	fi
	docker run --rm -it -p 8000:8000 $(IMAGE) $(ARGS)

# Run the Python script directly with arguments
.PHONY: run-direct
run-direct:
	python mcp_mediawiki.py $(ARGS)

# Run with interactive shell inside container
.PHONY: shell
shell:
	docker run --rm -it $(IMAGE) /bin/bash

# Display network information
.PHONY: network-info
network-info:
	@echo "Displaying Docker network information:"
	docker network ls
	@echo "\nNetwork details for mcp_network:"
	docker network inspect mcp-mediawiki_mcp_network

# Display container IP information
.PHONY: container-ip
container-ip:
	@echo "Container network information:"
	docker compose exec mcp-mediawiki ip addr show

# Stop the Docker container
.PHONY: down
down:
	docker compose down

# Rebuild and restart the container
.PHONY: rebuild
rebuild: build down up

# Show running containers
.PHONY: ps
ps:
	docker compose ps

# View logs
.PHONY: logs
logs:
	docker compose logs

# Follow logs
.PHONY: logs-follow
logs-follow:
	docker compose logs -f

# Clean up docker resources
.PHONY: clean
clean:
	docker compose down --rmi local

# Show help
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  make build        - Build the Docker image (tagged as $(IMAGE))"
	@echo "  make up           - Start the container using docker-compose"
	@echo "  make up-detached  - Start the container in detached mode"
	@echo "  make run-args     - Run with custom arguments: make run-args ARGS=\"--api-host=wiki.example.org\""
	@echo "  make run-direct   - Run Python script directly: make run-direct ARGS=\"--api-host=wiki.example.org\""
	@echo "  make shell        - Start a shell in the Docker container"
	@echo "  make network-info - Display Docker network information"
	@echo "  make container-ip - Display container IP address information"
	@echo "  make down         - Stop the running container"
	@echo "  make rebuild      - Rebuild and restart the container"
	@echo "  make ps           - Show running container status"
	@echo "  make logs         - View container logs"
	@echo "  make logs-follow  - Follow container logs"
	@echo "  make clean        - Remove container and local images"
	@echo "  make help         - Show this help message"
