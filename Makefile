# Sovereign AgentOps — Community Edition Makefile

.PHONY: all test coverage lint docker-build docker-run clean \
        build publish publish-docker publish-pypi

all: test

test:
	python3 -m pytest -v --tb=short

coverage:
	python3 -m pytest --cov=tools --cov-report=term-missing --cov-report=html

lint:
	python3 -m py_compile tools/mcp_server.py
	python3 -m py_compile cli/receipt-verify.py

docker-build:
	docker build -t agentops-community -f Dockerfile ..

docker-run:
	docker compose up --build

clean:
	rm -rf __pycache__ */__pycache__ tests/__pycache__
	rm -rf .pytest_cache htmlcov .coverage
	rm -rf tools/__pycache__ cli/__pycache__
	rm -rf dist build *.egg-info

# ── Build & Publish ─────────────────────────────────────────────────

build:
	pip install build 2>/dev/null
	python3 -m build --sdist --wheel
	@echo "\nBuild artifacts in dist/:"
	ls -la dist/

# Publish to test PyPI first, then real PyPI
publish-test:
	pip install twine 2>/dev/null
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

publish-pypi:
	pip install twine 2>/dev/null
	twine upload dist/*

publish-docker:
	docker build -t $(DOCKER_USER)/agentops-community:latest -f Dockerfile ..
	docker push $(DOCKER_USER)/agentops-community:latest

publish: build publish-pypi publish-docker
	@echo "Community Edition published!"
