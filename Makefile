# ╔══════════════════════════════════════════════════════════════════╗
# ║  TechContent AI — Makefile                                       ║
# ║  Docker + Local development shortcuts                            ║
# ╚══════════════════════════════════════════════════════════════════╝

.PHONY: help up down restart logs logs-backend logs-frontend logs-ml \
        build build-backend build-frontend build-ml \
        local-backend local-frontend local-ml infra \
        clean nuke db-shell

# ── Default ─────────────────────────────────────────────────────────
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ═══════════════════════════════════════════════════════════════════
#  DOCKER — Full stack
# ═══════════════════════════════════════════════════════════════════

up: ## Start all services (build if needed)
	docker compose up -d --build

down: ## Stop all services
	docker compose down

restart: ## Restart all services
	docker compose restart

rebuild: ## Force rebuild all images (no cache)
	docker compose build --no-cache && docker compose up -d

# ── Build individual images ─────────────────────────────────────────

build-backend: ## Build backend image only
	docker compose build backend

build-frontend: ## Build frontend image only
	docker compose build frontend

build-ml: ## Build ML service image only
	docker compose build ml-service

# ── Logs ────────────────────────────────────────────────────────────

logs: ## Follow logs for all services
	docker compose logs -f

logs-backend: ## Follow backend logs
	docker compose logs -f backend

logs-frontend: ## Follow frontend logs
	docker compose logs -f frontend

logs-ml: ## Follow ML service logs
	docker compose logs -f ml-service

logs-db: ## Follow database logs
	docker compose logs -f db

# ═══════════════════════════════════════════════════════════════════
#  LOCAL — Run services natively (infra stays in Docker)
# ═══════════════════════════════════════════════════════════════════

infra: ## Start only infrastructure (DB + Supabase Auth/REST/Studio)
	docker compose up -d db supabase-auth supabase-rest supabase-meta
	@echo ""
	@echo "  Infraestructura lista:"
	@echo "    PostgreSQL     → localhost:5433"
	@echo "    Supabase Auth  → localhost:9999"
	@echo "    Supabase REST  → localhost:3000"
	@echo "    Supabase Studio→ localhost:8000"
	@echo ""

local-backend: infra ## Run Spring Boot locally (needs infra)
	cd backend && ./mvnw spring-boot:run

local-frontend: ## Run Next.js dev server (bun)
	cd frontend/techisolutions && bun run dev

local-ml: ## Run FastAPI GraphRAG service locally (needs Python venv)
	cd datascience/proyecto && PYTHONPATH=src python -m uvicorn src.api.app:app --reload --host 0.0.0.0 --port 5000

local-all: infra ## Run all services locally (in parallel, needs tmux)
	@echo "Iniciando servicios locales..."
	@tmux new-session -d -s techcontent 'cd backend && ./mvnw spring-boot:run' \; \
		split-window -h 'cd frontend/techisolutions && bun run dev' \; \
		split-window -v 'cd datascience/proyecto && PYTHONPATH=src python -m uvicorn src.api.app:app --reload --host 0.0.0.0 --port 5000' \; \
		select-layout even-horizontal \; \
		attach
	@echo "  Si no tenes tmux, abri 3 terminales y ejecutá:"
	@echo "    make local-backend"
	@echo "    make local-frontend"
	@echo "    make local-ml"

# ═══════════════════════════════════════════════════════════════════
#  UTILS
# ═══════════════════════════════════════════════════════════════════

db-shell: ## Open psql shell into PostgreSQL
	docker compose exec db psql -U postgres -d techcontent

clean: ## Remove stopped containers and dangling images
	docker compose down --remove-orphans
	docker image prune -f

nuke: ## Destroy everything (volumes included!)
	docker compose down -v --remove-orphans
	docker image prune -f

status: ## Show running containers
	docker compose ps
