# ============================================================================
# WebMirror - Self-Documenting Makefile
# ============================================================================
#
# This Makefile uses 'uv' for lightning-fast dependency management
# Run 'make' or 'make help' to see all available commands
#
# Author: Ruslan Magana
# Website: ruslanmv.com
# ============================================================================

.PHONY: help install dev test lint format audit clean run docker-build docker-run

# ANSI color codes for beautiful output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Default target - show help
.DEFAULT_GOAL := help

## help: Display this help message
help:
	@echo "$(BLUE)╔═══════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║$(NC)  $(GREEN)WebMirror - A Blazingly Fast Website Cloning Engine$(NC)      $(BLUE)║$(NC)"
	@echo "$(BLUE)╚═══════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(YELLOW)Available commands:$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf ""} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo ""

##@ 🚀 Development

## install: Install production dependencies using uv
install:
	@echo "$(BLUE)📦 Installing production dependencies with uv...$(NC)"
	@command -v uv >/dev/null 2>&1 || { echo "$(RED)Error: uv is not installed. Visit https://github.com/astral-sh/uv$(NC)"; exit 1; }
	uv pip install -e .
	@echo "$(GREEN)✓ Installation complete!$(NC)"

## dev: Install development dependencies
dev:
	@echo "$(BLUE)🔧 Installing development dependencies...$(NC)"
	@command -v uv >/dev/null 2>&1 || { echo "$(RED)Error: uv is not installed.$(NC)"; exit 1; }
	uv pip install -e ".[dev]"
	@echo "$(GREEN)✓ Development environment ready!$(NC)"

## start: Run WebMirror CLI
start:
	@echo "$(BLUE)🚀 Starting WebMirror...$(NC)"
	python -m webmirror.cli --help

## run: Quick clone example (example.com)
run:
	@echo "$(BLUE)🌐 Running example clone...$(NC)"
	python -m webmirror.cli clone https://example.com --max-pages 5 -o ./demo_output

##@ 🎨 GUI Interface

## install-gui: Install with GUI dependencies
install-gui:
	@echo "$(BLUE)📦 Installing WebMirror with GUI support...$(NC)"
	@command -v uv >/dev/null 2>&1 || { echo "$(RED)Error: uv is not installed.$(NC)"; exit 1; }
	uv pip install -e ".[gui]"
	@echo "$(GREEN)✓ GUI dependencies installed!$(NC)"

## gui: Launch the Web GUI
gui:
	@echo "$(BLUE)🎨 Starting WebMirror Web GUI...$(NC)"
	@echo "$(YELLOW)Opening in your browser...$(NC)"
	@echo ""
	@streamlit run src/webmirror/gui/streamlit_app.py

## gui-dev: Launch GUI with dev dependencies
gui-dev:
	@echo "$(BLUE)🎨 Starting WebMirror GUI (dev mode)...$(NC)"
	@command -v uv >/dev/null 2>&1 || { echo "$(RED)Error: uv is not installed.$(NC)"; exit 1; }
	uv pip install -e ".[gui,dev]"
	streamlit run src/webmirror/gui/streamlit_app.py --server.runOnSave true

##@ 🧪 Testing & Quality

## test: Run tests with pytest
test:
	@echo "$(BLUE)🧪 Running tests...$(NC)"
	pytest tests/ -v --cov=src/webmirror --cov-report=term-missing
	@echo "$(GREEN)✓ Tests complete!$(NC)"

## test-fast: Run tests without coverage
test-fast:
	@echo "$(BLUE)⚡ Running fast tests...$(NC)"
	pytest tests/ -v --no-cov
	@echo "$(GREEN)✓ Tests complete!$(NC)"

## lint: Run ruff linter
lint:
	@echo "$(BLUE)🔍 Running ruff linter...$(NC)"
	ruff check src/ tests/
	@echo "$(GREEN)✓ Linting complete!$(NC)"

## format: Format code with ruff
format:
	@echo "$(BLUE)✨ Formatting code with ruff...$(NC)"
	ruff format src/ tests/
	ruff check --fix src/ tests/
	@echo "$(GREEN)✓ Code formatted!$(NC)"

## typecheck: Run mypy type checker
typecheck:
	@echo "$(BLUE)🔬 Running mypy type checker...$(NC)"
	mypy src/
	@echo "$(GREEN)✓ Type checking complete!$(NC)"

## audit: Run comprehensive quality checks (lint + typecheck + security)
audit: lint typecheck
	@echo "$(BLUE)🔒 Running security audit with bandit...$(NC)"
	bandit -r src/ -ll
	@echo "$(GREEN)✓ Security audit complete!$(NC)"
	@echo ""
	@echo "$(GREEN)✨ All quality checks passed!$(NC)"

##@ 🐳 Docker

## docker-build: Build Docker image
docker-build:
	@echo "$(BLUE)🐳 Building Docker image...$(NC)"
	docker build -t webmirror:latest .
	@echo "$(GREEN)✓ Docker image built!$(NC)"

## docker-run: Run WebMirror in Docker
docker-run:
	@echo "$(BLUE)🐳 Running WebMirror in Docker...$(NC)"
	docker run --rm -v $(PWD)/output:/data webmirror:latest clone https://example.com --max-pages 5

## docker-shell: Open shell in Docker container
docker-shell:
	@echo "$(BLUE)🐳 Opening shell in Docker container...$(NC)"
	docker run --rm -it -v $(PWD)/output:/data --entrypoint /bin/bash webmirror:latest

##@ 🧹 Maintenance

## clean: Remove build artifacts and cache files
clean:
	@echo "$(BLUE)🧹 Cleaning up...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ .coverage 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete!$(NC)"

## clean-all: Deep clean including output directories
clean-all: clean
	@echo "$(BLUE)🧹 Deep cleaning...$(NC)"
	rm -rf website_mirror/ demo_output/ output/ 2>/dev/null || true
	@echo "$(GREEN)✓ Deep cleanup complete!$(NC)"

##@ 📦 Distribution

## build: Build distribution packages
build: clean
	@echo "$(BLUE)📦 Building distribution packages...$(NC)"
	python -m build
	@echo "$(GREEN)✓ Build complete! Check dist/ directory$(NC)"

## publish: Publish to PyPI (requires credentials)
publish: build
	@echo "$(BLUE)📤 Publishing to PyPI...$(NC)"
	twine upload dist/*
	@echo "$(GREEN)✓ Published to PyPI!$(NC)"

##@ 📊 Reports

## coverage: Generate HTML coverage report
coverage:
	@echo "$(BLUE)📊 Generating coverage report...$(NC)"
	pytest tests/ --cov=src/webmirror --cov-report=html
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/index.html$(NC)"
	@command -v open >/dev/null 2>&1 && open htmlcov/index.html || true

## benchmark: Run performance benchmarks
benchmark:
	@echo "$(BLUE)⚡ Running benchmarks...$(NC)"
	@echo "$(YELLOW)Benchmarking example.com clone...$(NC)"
	time python -m webmirror.cli clone https://example.com --max-pages 10 -o ./benchmark_output
	@echo "$(GREEN)✓ Benchmark complete!$(NC)"
