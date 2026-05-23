# ─────────────────────────────────────────────────────────────────────────────
# Makefile — JEE Dropout Prediction System
#
# Targets
# ───────
#   make setup    → copy .env files from examples (first-time setup)
#   make train    → train ML models and save to models/
#   make dev      → start full stack with Docker Compose
#   make dev-local → run backend + frontend locally without Docker
#   make test     → run pytest suite with coverage
#   make seed     → seed the database with demo data
#   make migrate  → apply pending Alembic migrations
#   make lint     → run ruff linter on backend/
#   make clean    → remove Python cache, test DBs, build artefacts
#   make logs     → tail docker-compose logs
#   make shell    → open a bash shell inside the backend container
#   make psql     → connect to the PostgreSQL container
#
# Usage example (first time)
# ──────────────────────────
#   make setup
#   make train
#   make dev
#
# ─────────────────────────────────────────────────────────────────────────────

# Use bash for all shell commands (safer than /bin/sh for complex scripts)
SHELL := /bin/bash
.DEFAULT_GOAL := help

# ── Colours for pretty output ─────────────────────────────────────────────────
BOLD   := \033[1m
GREEN  := \033[32m
YELLOW := \033[33m
CYAN   := \033[36m
RESET  := \033[0m

# ── Python / pip executable ───────────────────────────────────────────────────
PYTHON  := python
PIP     := $(PYTHON) -m pip
PYTEST  := $(PYTHON) -m pytest
ALEMBIC := $(PYTHON) -m alembic

# ── Docker Compose command (v2 plugin style) ──────────────────────────────────
DC := docker compose

# ─────────────────────────────────────────────────────────────────────────────
.PHONY: help setup train dev dev-local test seed migrate lint clean logs shell psql

# ── help: print all targets with descriptions ────────────────────────────────
help:
	@echo ""
	@echo "$(BOLD)$(CYAN)JEE Dropout Prediction System$(RESET)"
	@echo "$(YELLOW)Usage: make <target>$(RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-14s$(RESET) %s\n", $$1, $$2}'
	@echo ""


# ── setup: copy .env.example files so the user can fill in secrets ────────────
setup: ## Copy .env.example → .env files (run once on first clone)
	@echo "$(CYAN)Setting up environment files...$(RESET)"
	@if [ ! -f backend/.env ]; then \
		cp backend/.env.example backend/.env; \
		echo "  Created backend/.env — fill in your secrets!"; \
	else \
		echo "  backend/.env already exists — skipping"; \
	fi
	@if [ ! -f frontend/.env ]; then \
		cp frontend/.env.example frontend/.env; \
		echo "  Created frontend/.env"; \
	else \
		echo "  frontend/.env already exists — skipping"; \
	fi
	@mkdir -p models data reports uploads logs migrations/versions
	@echo "$(GREEN)Setup complete! Edit backend/.env before starting.$(RESET)"


# ── train: run the ML training script ────────────────────────────────────────
train: ## Train ML models and save .pkl files to models/
	@echo "$(CYAN)Training ML models...$(RESET)"
	$(PYTHON) ml_training/train.py
	@echo "$(GREEN)Training complete! Models saved to models/$(RESET)"


# ── dev: start the full stack with Docker Compose ────────────────────────────
dev: ## Start full stack (Docker): db + backend + frontend + nginx
	@echo "$(CYAN)Starting Docker Compose stack...$(RESET)"
	$(DC) up --build -d
	@echo ""
	@echo "$(GREEN)Stack is running!$(RESET)"
	@echo "  Frontend → http://localhost"
	@echo "  API Docs → http://localhost/api/docs"
	@echo "  Health   → http://localhost/health"
	@echo ""
	@echo "Run '$(YELLOW)make logs$(RESET)' to follow logs."


# ── dev-local: run backend and frontend locally without Docker ────────────────
dev-local: ## Run backend + frontend locally (no Docker required)
	@echo "$(CYAN)Starting local dev servers...$(RESET)"
	@echo "  Backend  → http://localhost:8000"
	@echo "  Frontend → http://localhost:5173"
	# Run backend in background, start frontend in foreground
	$(PYTHON) -m uvicorn backend.app.main:app --reload --port 8000 &
	cd frontend && npm run dev


# ── test: run the pytest suite ────────────────────────────────────────────────
test: ## Run pytest with coverage report
	@echo "$(CYAN)Running tests...$(RESET)"
	$(PYTEST) tests/ \
		--cov=backend/app \
		--cov-report=term-missing \
		--cov-report=html:htmlcov \
		-v
	@echo "$(GREEN)Coverage report saved to htmlcov/index.html$(RESET)"


# ── seed: seed the database with demo data ────────────────────────────────────
seed: ## Seed the database (1 institute, 3 batches, 20 students + ML predictions)
	@echo "$(CYAN)Seeding database...$(RESET)"
	$(PYTHON) -m backend.app.utils.db_seed
	@echo "$(GREEN)Seed complete!$(RESET)"


# ── migrate: apply Alembic migrations ────────────────────────────────────────
migrate: ## Apply pending Alembic migrations (alembic upgrade head)
	@echo "$(CYAN)Running Alembic migrations...$(RESET)"
	$(ALEMBIC) upgrade head
	@echo "$(GREEN)Migrations applied.$(RESET)"


# ── lint: run ruff on the backend ────────────────────────────────────────────
lint: ## Lint backend/ with ruff (warnings only — does not block)
	@echo "$(CYAN)Linting backend/...$(RESET)"
	$(PYTHON) -m ruff check backend/ --ignore E501 || true


# ── clean: remove generated artefacts ────────────────────────────────────────
clean: ## Remove __pycache__, *.pyc, test DBs, coverage, build artefacts
	@echo "$(CYAN)Cleaning...$(RESET)"
	find . -type d -name __pycache__  -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc"      -delete 2>/dev/null             || true
	find . -type f -name "*.pyo"      -delete 2>/dev/null             || true
	find . -type f -name "*.db"       -delete 2>/dev/null             || true
	rm -rf .pytest_cache htmlcov .coverage coverage.xml frontend/dist
	@echo "$(GREEN)Clean complete.$(RESET)"


# ── logs: tail docker-compose logs ───────────────────────────────────────────
logs: ## Tail Docker Compose logs (all services)
	$(DC) logs -f


# ── shell: open a bash shell in the backend container ────────────────────────
shell: ## Open bash inside the running backend container
	$(DC) exec backend bash


# ── psql: open psql inside the db container ──────────────────────────────────
psql: ## Connect to PostgreSQL inside the db container
	$(DC) exec db psql -U jee_user -d jee_dropout_db
