# PolicyClaw — judge- and CI-friendly command surface.
# Targets run under bash (Git Bash on Windows; any sh/bash elsewhere).

SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help

# ---- python venv / interpreter discovery ----------------------------------
# Prefer the project venv at backend/.venv. Fall back to whatever `python` is
# on PATH so fresh clones print a helpful error from pip instead of make's.
ifeq ($(OS),Windows_NT)
VENV_PY := backend/.venv/Scripts/python.exe
else
VENV_PY := backend/.venv/bin/python
endif
PY := $(if $(wildcard $(VENV_PY)),$(VENV_PY),python)

# ---- meta -----------------------------------------------------------------
.PHONY: help
help:
	@echo "PolicyClaw Make targets"
	@echo "  make install       Install backend + frontend dependencies"
	@echo "  make dev-backend   uvicorn app.main:app --reload (port 8000)"
	@echo "  make dev-frontend  next dev (port 3000)"
	@echo "  make test          pytest backend/tests/ -q"
	@echo "  make lint          ruff + npm run lint"
	@echo "  make evals         python evals/run.py"
	@echo "  make ci-local      test + lint + build + evals (mirrors CI)"

# ---- install --------------------------------------------------------------
.PHONY: install
install:
	$(PY) -m pip install -r backend/requirements.txt
	npm ci --prefix frontend

# ---- dev loops ------------------------------------------------------------
.PHONY: dev-backend
dev-backend:
	cd backend && $(PY) -m uvicorn app.main:app --reload

.PHONY: dev-frontend
dev-frontend:
	npm run dev --prefix frontend

# ---- checks ---------------------------------------------------------------
.PHONY: test
test:
	$(PY) -m pytest backend/tests/ -q

.PHONY: lint
lint:
	$(PY) -m ruff check backend/
	npm run lint --prefix frontend

.PHONY: evals
evals:
	$(PY) evals/run.py

.PHONY: build
build:
	npm run build --prefix frontend

# ---- CI ------------------------------------------------------------------
# Mirrors .github/workflows/ci.yml: backend tests, backend smoke-import,
# frontend build. `lint` is informational in CI too.
.PHONY: ci-local
ci-local: test lint build evals
	@echo "ci-local: all green"
