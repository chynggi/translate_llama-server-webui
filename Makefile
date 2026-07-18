.PHONY: install middleware web test dev

install:
	cd apps/middleware && python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
	cd apps/web && npm install

middleware:
	cd apps/middleware && . .venv/bin/activate && uvicorn translator_studio.main:app --reload --host 127.0.0.1 --port 8000

web:
	cd apps/web && npm run dev

test:
	cd apps/middleware && . .venv/bin/activate && pytest

dev:
	$(MAKE) middleware & $(MAKE) web
