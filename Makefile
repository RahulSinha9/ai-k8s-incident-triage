.PHONY: install test run docker-build

install:
	pip install -r requirements.txt

test:
	pytest -q

run:
	uvicorn app.main:app --reload --port 8000

docker-build:
	docker build -t ai-k8s-incident-triage:latest .
