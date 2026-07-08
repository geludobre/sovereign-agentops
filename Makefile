# Sovereign AgentOps — Community Edition Makefile

.PHONY: all test coverage lint docker-build docker-run clean

all: test

test:
	python3 -m pytest -v --tb=short

coverage:
	python3 -m pytest --cov=tools --cov-report=term-missing --cov-report=html

lint:
	python3 -m py_compile tools/mcp-server.py
	python3 -m py_compile cli/receipt-verify.py

docker-build:
	docker build -t agentops-community -f Dockerfile ..

docker-run:
	docker compose up --build

clean:
	rm -rf __pycache__ */__pycache__ tests/__pycache__
	rm -rf .pytest_cache htmlcov .coverage
	rm -rf tools/__pycache__ cli/__pycache__
