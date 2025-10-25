PYTHON := python
PIP := pip

.PHONY: install run-backend lint format test download-model

install:
	$(PIP) install -r requirements.txt

download-model:
	$(PYTHON) -m spacy download en_core_web_lg || $(PYTHON) -m spacy download en_core_web_sm

run-backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

lint:
	ruff check backend
	isort backend --check-only
	black backend --check

format:
	isort backend
	black backend

test:
	pytest
