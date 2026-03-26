BACKEND_HOST ?= 127.0.0.1
BACKEND_PORT ?= 8040
FRONTEND_PORT ?= 3040
DOMAIN ?= reddash

.PHONY: help install backend-install frontend-install dev backend frontend \
	generate-data generate-models load-data setup-surface validate-domain smoke-domain create-domain flush-redis reset

help:
	@echo "Targets:"
	@echo "  make install          Install backend and frontend dependencies"
	@echo "  make generate-models  Regenerate Context Surface model file for DOMAIN=$(DOMAIN)"
	@echo "  make generate-data    Generate sample JSONL data into output/DOMAIN"
	@echo "  make setup-surface    Register Redis, create surface & agent key via ctxctl"
	@echo "  make load-data        Load output/DOMAIN/*.jsonl into Redis + Search indexes"
	@echo "  make validate-domain  Validate the active domain pack"
	@echo "  make smoke-domain     Generate models/data and verify the domain structure"
	@echo "  make create-domain    Scaffold a new domain pack for DOMAIN=$(DOMAIN)"
	@echo "  make flush-redis      Flush the Redis database (FLUSHDB)"
	@echo "  make reset            Flush Redis + recreate surface + reload data"
	@echo "  make backend          Start FastAPI backend"
	@echo "  make frontend         Start Vite frontend"
	@echo "  make dev              Run backend and frontend together"

backend-install:
	@uv sync

frontend-install:
	@cd frontend && npm install

install: backend-install frontend-install

generate-models:
	@uv run python scripts/generate_models.py --domain $(DOMAIN)

generate-data:
	@uv run python scripts/generate_data.py --domain $(DOMAIN)

load-data:
	@uv run python scripts/load_data.py --domain $(DOMAIN)

setup-surface:
	@uv run python scripts/setup_surface.py --domain $(DOMAIN)

validate-domain:
	@uv run python scripts/validate_domain.py --domain $(DOMAIN)

smoke-domain:
	@uv run python scripts/smoke_domain.py --domain $(DOMAIN)

create-domain:
	@uv run python scripts/create_domain.py $(DOMAIN)

backend:
	@uv run uvicorn backend.app.main:app --reload --host $(BACKEND_HOST) --port $(BACKEND_PORT)

frontend:
	@cd frontend && npm run dev -- --host 0.0.0.0 --port $(FRONTEND_PORT)

flush-redis:
	@uv run python -c "\
	from backend.app.settings import get_settings; \
	from backend.app.redis_connection import create_redis_client; \
	s = get_settings(); r = create_redis_client(s); \
	r.flushdb(); \
	print('Flushed Redis at %s:%d/%d' % (s.redis_host, s.redis_port, s.redis_db))"
	@echo ""
	@echo "⚠️  Redis flushed. Context Surface indexes are gone."
	@echo "   Run 'make reset' or 'make setup-surface && make load-data' to recover."

reset: flush-redis
	@echo "Clearing old surface credentials..."
	@sed -i '' 's/^CTX_SURFACE_ID=.*/CTX_SURFACE_ID=/' .env
	@sed -i '' 's/^MCP_AGENT_KEY=.*/MCP_AGENT_KEY=/' .env
	@$(MAKE) setup-surface
	@$(MAKE) load-data
	@echo ""
	@echo "✅ Reset complete. Run 'make dev' to start."

dev:
	@trap 'kill 0' EXIT; $(MAKE) backend & $(MAKE) frontend & wait
