# ============================================================================
# WebClone - Self-Documenting Makefile
# ============================================================================
#
# This Makefile uses 'uv' for lightning-fast dependency management
# Run 'make' or 'make help' to see all available commands
#
# Author: Ruslan Magana
# Website: ruslanmv.com
# ============================================================================

.PHONY: help uv-ensure ensure-tk install install-all dev start run \
        install-gui gui gui-dev \
        install-mcp mcp mcp-dev \
        test test-fast lint format typecheck audit \
        clean clean-all \
        docker-build docker-run docker-shell \
        build publish coverage benchmark check-patch apply-patch

# Keep recipe output plain for cross-platform shells (especially native Windows cmd.exe).
BLUE :=
GREEN :=
YELLOW :=
RED :=
NC :=

ifeq ($(OS),Windows_NT)
PATH_SEP := ;
VENV_BIN := .venv/Scripts
VENV_PYTHON := $(VENV_BIN)/python.exe
else
PATH_SEP := :
VENV_BIN := .venv/bin
VENV_PYTHON := $(VENV_BIN)/python
endif

# Python interpreter (override with: make PYTHON=python3 ...).
# Prefer the uv-created virtualenv so `make run` works immediately after `make install`.
PYTHON ?= $(if $(wildcard $(VENV_PYTHON)),$(VENV_PYTHON),python)
PATCH ?= changes.patch

# Make the src-layout package importable from a checkout as a fallback, even if
# editable installation failed or the caller's Python is not the virtualenv Python.
export PYTHONPATH := src$(if $(PYTHONPATH),$(PATH_SEP)$(PYTHONPATH),)

# Default target - show help
.DEFAULT_GOAL := help

# Windows-safe help: no ANSI codes, plain echo
help: ## Display this help message
	@echo "============================================================"
	@echo " WebClone - A Blazingly Fast Website Cloning Engine"
	@echo "============================================================"
	@echo
	@echo "Available commands:"
	@echo
	@echo "  help               Display this help message"
	@echo "  install            Install production dependencies (CLI only)"
	@echo "  install-all        Install CLI + GUI + MCP (all-in-one)"
	@echo "  dev                Install development dependencies"
	@echo "  start              Run WebClone CLI help"
	@echo "  run                Run example clone on example.com"
	@echo "  install-gui        Install GUI dependencies"
	@echo "  gui                Launch the Enterprise Desktop GUI"
	@echo "  gui-dev            Launch GUI with dev dependencies"
	@echo "  install-mcp        Install MCP server dependencies"
	@echo "  mcp                Launch the MCP server"
	@echo "  mcp-dev            Install MCP server with dev tools"
	@echo "  test               Run tests with coverage"
	@echo "  test-fast          Run tests without coverage"
	@echo "  lint               Run ruff linter"
	@echo "  format             Format code with ruff"
	@echo "  typecheck          Run mypy type checker"
	@echo "  audit              Lint + typecheck + security audit"
	@echo "  docker-build       Build Docker image"
	@echo "  docker-run         Run WebClone in Docker"
	@echo "  docker-shell       Open shell in Docker container"
	@echo "  clean              Remove build artifacts and cache files"
	@echo "  clean-all          Deep clean including output directories"
	@echo "  build              Build distribution packages"
	@echo "  publish            Publish to PyPI"
	@echo "  coverage           Generate HTML coverage report"
	@echo "  benchmark          Run performance benchmarks"
	@echo "  check-patch        Check changes.patch, treating already-applied as OK"
	@echo "  apply-patch        Apply changes.patch with whitespace fixes"
	@echo

# Internal: ensure uv exists and a .venv is created
# Cross-platform: just let 'uv venv .venv' do the work; if uv is missing, this will fail.
uv-ensure:
	@echo "Ensuring uv and virtual environment in .venv..."
	@uv venv .venv || (echo "Error: uv is not installed or failed. See https://github.com/astral-sh/uv" && exit 1)

# Cross-platform: ensure Tkinter is available for GUI use
ensure-tk: ## Ensure Tkinter is available for GUI use
	@echo "Checking for Tkinter (GUI support)..."
	@$(PYTHON) -c "import tkinter" || (echo "Tkinter is NOT available in this Python interpreter. Install Tk support for your OS (e.g. python.org installer on Windows/macOS, or python3-tk on Linux) and recreate your virtualenv." && exit 1)

##@ 🚀 Development

install: uv-ensure ## Install production dependencies using uv (CLI only)
	@echo $(BLUE)Installing production dependencies with uv...$(NC)
	uv pip install -e .
	@echo $(GREEN)Installation complete!$(NC)

install-all: uv-ensure ## Install CLI + GUI + MCP (all-in-one)
	@echo "$(BLUE)📦 Installing WebClone CLI + GUI + MCP...$(NC)"
	uv pip install -e ".[gui,mcp]"
	@echo "$(GREEN)✓ All WebClone components installed in the current Python environment!$(NC)"
	@$(MAKE) ensure-tk
	@echo ""
	@echo "$(YELLOW)📖 Next steps for MCP (Claude Desktop):$(NC)"
	@echo "  Add to ~/.config/claude/config.json:"
	@echo "    {\"mcpServers\": {\"webclone\": {\"command\": \"webclone-mcp\"}}}"
	@echo ""
	@echo "  Then you can run:"
	@echo "    - CLI: webclone ..."
	@echo "    - GUI: make gui"
	@echo "    - MCP: make mcp"

dev: uv-ensure ## Install development dependencies
	@echo "$(BLUE)🔧 Installing development dependencies...$(NC)"
	uv pip install -e ".[dev]"
	@echo "$(GREEN)✓ Development environment ready!$(NC)"

start: ## Run WebClone CLI
	@echo $(BLUE)Starting WebClone...$(NC)
	$(PYTHON) -m webclone.cli --help

run: ## Quick clone example (example.com)
	@echo $(BLUE)Running example clone...$(NC)
	$(PYTHON) -m webclone.cli clone https://example.com --max-pages 5 -o ./demo_output

##@ 🎨 GUI Interface

install-gui: uv-ensure ## Install with GUI dependencies
	@echo "$(BLUE)📦 Installing WebClone with GUI support...$(NC)"
	uv pip install -e ".[gui]"
	@echo "$(GREEN)✓ GUI Python dependencies installed!$(NC)"
	@$(MAKE) ensure-tk

gui: ## Launch the Enterprise Desktop GUI
	@echo "$(BLUE)🎨 Starting WebClone Enterprise Desktop GUI...$(NC)"
	-@$(PYTHON) -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('src').rglob('__pycache__')]"
	$(PYTHON) webclone-gui.py

gui-dev: uv-ensure ## Launch GUI with dev dependencies
	@echo "$(BLUE)🎨 Starting WebClone GUI (dev mode)...$(NC)"
	uv pip install -e ".[gui,dev]"
	$(PYTHON) webclone-gui.py

##@ 🤖 MCP Server (AI Agents)

install-mcp: uv-ensure ## Install MCP server dependencies
	@echo "$(BLUE)🤖 Installing WebClone MCP server...$(NC)"
	uv pip install -e ".[mcp]"
	@echo "$(GREEN)✓ MCP server dependencies installed!$(NC)"
	@echo ""
	@echo "$(YELLOW)📖 Next steps:$(NC)"
	@echo "  1. Add to Claude Desktop config (~/.config/claude/config.json):"
	@echo "     {\"mcpServers\": {\"webclone\": {\"command\": \"webclone-mcp\"}}}"
	@echo ""
	@echo "  2. Or run standalone: make mcp"
	@echo ""

mcp: ## Launch the MCP server for AI agents
	@echo "$(BLUE)🤖 Starting WebClone MCP Server...$(NC)"
	@echo "$(YELLOW)💡 Server runs on stdio - use with MCP clients$(NC)"
	@echo ""
	$(PYTHON) -m webclone.mcp

mcp-dev: uv-ensure ## Install MCP with dev dependencies
	@echo "$(BLUE)🤖 Installing MCP server with dev tools...$(NC)"
	uv pip install -e ".[mcp,dev]"
	@echo "$(GREEN)✓ MCP development environment ready!$(NC)"


check-patch: ## Check a patch with whitespace cleanup and already-applied detection
	$(PYTHON) scripts/apply_patch.py --check $(PATCH)

apply-patch: ## Apply a patch with whitespace cleanup and already-applied detection
	$(PYTHON) scripts/apply_patch.py $(PATCH)

##@ 🧪 Testing & Quality

test: ## Run tests with pytest
	@echo "$(BLUE)🧪 Running tests...$(NC)"
	pytest tests/ -v --cov=src/webclone --cov-report=term-missing
	@echo "$(GREEN)✓ Tests complete!$(NC)"

test-fast: ## Run tests without coverage
	@echo "$(BLUE)⚡ Running fast tests...$(NC)"
	pytest tests/ -v --no-cov
	@echo "$(GREEN)✓ Tests complete!$(NC)"

lint: ## Run ruff linter
	@echo "$(BLUE)🔍 Running ruff linter...$(NC)"
	ruff check src/ tests/
	@echo "$(GREEN)✓ Linting complete!$(NC)"

format: ## Format code with ruff
	@echo "$(BLUE)✨ Formatting code with ruff...$(NC)"
	ruff format src/ tests/
	ruff check --fix src/ tests/
	@echo "$(GREEN)✓ Code formatted!$(NC)"

typecheck: ## Run mypy type checker
	@echo "$(BLUE)🔬 Running mypy type checker...$(NC)"
	mypy src/
	@echo "$(GREEN)✓ Type checking complete!$(NC)"

audit: lint typecheck ## Run comprehensive quality checks (lint + typecheck + security)
	@echo "$(BLUE)🔒 Running security audit with bandit...$(NC)"
	bandit -r src/ -ll
	@echo "$(GREEN)✓ Security audit complete!$(NC)"
	@echo ""
	@echo "$(GREEN)✨ All quality checks passed!$(NC)"

##@ 🐳 Docker

docker-build: ## Build Docker image
	@echo "$(BLUE)🐳 Building Docker image...$(NC)"
	docker build -t webclone:latest .
	@echo "$(GREEN)✓ Docker image built!$(NC)"

docker-run: ## Run WebClone in Docker
	@echo "$(BLUE)🐳 Running WebClone in Docker...$(NC)"
	docker run --rm -v $(PWD)/output:/data webclone:latest clone https://example.com --max-pages 5

docker-shell: ## Open shell in Docker container
	@echo "$(BLUE)🐳 Opening shell in Docker container...$(NC)"
	docker run --rm -it -v $(PWD)/output:/data --entrypoint /bin/bash webclone:latest

##@ 🧹 Maintenance

clean: ## Remove build artifacts and cache files
	@echo "$(BLUE)🧹 Cleaning up...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ .coverage 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete!$(NC)"

clean-all: clean ## Deep clean including output directories
	@echo "$(BLUE)🧹 Deep cleaning...$(NC)"
	rm -rf website_mirror/ demo_output/ output/ 2>/dev/null || true
	@echo "$(GREEN)✓ Deep cleanup complete!$(NC)"

##@ 📦 Distribution

build: clean ## Build distribution packages
	@echo "$(BLUE)📦 Building distribution packages...$(NC)"
	$(PYTHON) -m build
	@echo "$(GREEN)✓ Build complete! Check dist/ directory$(NC)"

publish: build ## Publish to PyPI (requires credentials)
	@echo "$(BLUE)📤 Publishing to PyPI...$(NC)"
	twine upload dist/*
	@echo "$(GREEN)✓ Published to PyPI!$(NC)"

##@ 📊 Reports

coverage: ## Generate HTML coverage report
	@echo "$(BLUE)📊 Generating HTML coverage report...$(NC)"
	pytest tests/ --cov=src/webclone --cov-report=html
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/index.html$(NC)"
	command -v open >/dev/null 2>&1 && open htmlcov/index.html || true

benchmark: ## Run performance benchmarks
	@echo "$(BLUE)⚡ Running benchmarks...$(NC)"
	@echo "$(YELLOW)Benchmarking example.com clone...$(NC)"
	time $(PYTHON) -m webclone.cli clone https://example.com --max-pages 10 -o ./benchmark_output
	@echo "$(GREEN)✓ Benchmark complete!$(NC)"
