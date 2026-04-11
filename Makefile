.PHONY: build up down restart logs test shell clean

IMAGE   := pesnik/sandbox
COMPOSE := docker compose

# Build the image
build:
	$(COMPOSE) build

# Start (detached)
up:
	$(COMPOSE) up -d

# Stop + remove containers
down:
	$(COMPOSE) down

# Full rebuild + restart
restart: down build up

# Tail logs
logs:
	$(COMPOSE) logs -f sandbox

# Run E2E test suite (requires container to be up)
test:
	cd tests && pip install -q -r requirements.txt && pytest -v

# Shell into the running container
shell:
	docker exec -it sandbox bash

# Remove image and volumes
clean:
	$(COMPOSE) down -v --rmi local

# One-liner: build → up → test
ci: build up
	@echo "waiting for healthy..."
	@until docker inspect --format='{{.State.Health.Status}}' sandbox 2>/dev/null | grep -q healthy; do sleep 1; done
	$(MAKE) test
