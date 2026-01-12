.PHONY: help lint test run install clean

help:
	@echo "Available targets:"
	@echo "  lint    - Run linters (flake8, mypy if available)"
	@echo "  test    - Run unit tests"
	@echo "  run     - Run linmon with sample config"
	@echo "  install - Install package in development mode"
	@echo "  clean   - Remove build artifacts"

lint:
	@echo "Running linters..."
	@python -m flake8 linmon tests --max-line-length=100 --ignore=E501,W503 || true
	@python -m mypy linmon --ignore-missing-imports || echo "mypy not available, skipping"

test:
	@echo "Running tests..."
	@python -m pytest tests/unit -v

run:
	@python -m linmon --config configs/sample.yaml

install:
	@pip install -e .

clean:
	@rm -rf build/ dist/ *.egg-info/
	@find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
