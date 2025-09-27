.PHONY: build test clean install dev-install lint format

# Default Python interpreter
PYTHON := python3

# Virtual environment
VENV := venv
VENV_BIN := $(VENV)/bin

# Build targets
build: clean test
	@echo "Building Idle Security Reminder..."
	$(PYTHON) -m pip install --upgrade pip setuptools wheel
	$(PYTHON) -m pip install pyinstaller
	./scripts/build_all.sh

# Development setup
dev-install:
	$(PYTHON) -m venv $(VENV)
	$(VENV_BIN)/pip install --upgrade pip
	$(VENV_BIN)/pip install -r requirements.txt
	$(VENV_BIN)/pip install -r requirements-dev.txt
	$(VENV_BIN)/pip install -e .

# Install dependencies
install:
	$(PYTHON) -m pip install -r requirements.txt

# Run tests
test:
	$(PYTHON) -m pytest tests/ -v --cov=idle_reminder --cov-report=html

# Lint code
lint:
	$(PYTHON) -m flake8 src/ tests/
	$(PYTHON) -m mypy src/

# Format code
format:
	$(PYTHON) -m black src/ tests/
	$(PYTHON) -m isort src/ tests/

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Run application
run:
	$(PYTHON) -m idle_reminder

# Run in debug mode
debug:
	$(PYTHON) -m idle_reminder --debug

# Generate diagnostics
diagnostics:
	$(PYTHON) -m idle_reminder --diagnostics
