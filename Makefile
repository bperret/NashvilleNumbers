.PHONY: help install smoke-test clean-artifacts test dev

help:
	@echo "Nashville Numbers - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install Python dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make smoke-test       Run PDF conversion smoke test"
	@echo "  make test             Run full test suite"
	@echo ""
	@echo "Development:"
	@echo "  make dev              Start development server"
	@echo "  make clean-artifacts  Clean test artifacts"

install:
	pip install -r requirements.txt

smoke-test:
	python scripts/smoke_convert.py

test:
	pytest backend/tests/ -v

dev:
	uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000

clean-artifacts:
	rm -rf artifacts/
	@echo "Artifacts cleaned"
