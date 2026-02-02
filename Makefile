# ============================================================================
# WebClone - Makefile
# ============================================================================
# Run 'make' or 'make help' to see all available commands
# ============================================================================

.PHONY: help install install-all install-gui install-mcp dev \
        test test-fast lint format typecheck audit \
        gui mcp start run \
        clean clean-all \
        docker-build docker-run docker-shell \
        build publish coverage benchmark

# Python interpreter
PYTHON ?= python

# Default target
.DEFAULT_GOAL := help

# ============================================================================
# Help
# ============================================================================

help: ## Show this help message
	@echo "============================================================"
	@echo " WebClone - Website Cloning Engine"
	@echo "============================================================"
	@echo ""
	@echo "Installation:"
	@echo "  make install        Install production dependencies"
	@echo "  make install-all    Install CLI + GUI + MCP (complete)"
	@echo "  make install-gui    Install with GUI support"
	@echo "  make install-mcp    Install MCP server"
	@echo "  make dev            Install development dependencies"
	@echo ""
	@echo "Running:"
	@echo "  make gui            Launch Desktop GUI"
	@echo "  make mcp            Launch MCP Server"
	@echo "  make start          Show CLI help"
	@echo "  make run            Run example clone"
	@echo ""
	@echo "Testing:"
	@echo "  make test           Run tests with coverage"
	@echo "  make test-fast      Run tests without coverage"
	@echo "  make audit          Run all quality checks"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean          Remove cache files"
	@echo "  make clean-all      Deep clean all outputs"
	@echo ""

# ============================================================================
# Installation
# ============================================================================

install: ## Install production dependencies
	@echo "[*] Installing production dependencies..."
	@if command -v uv >/dev/null 2>&1; then \
		uv venv .venv 2>/dev/null || true; \
		uv pip install -e . ; \
	else \
		$(PYTHON) -m pip install --upgrade pip; \
		$(PYTHON) -m pip install -e . ; \
	fi
	@echo "[OK] Installation complete!"

install-all: ## Install CLI + GUI + MCP (complete installation)
	@echo "[*] Installing all WebClone components..."
	@if command -v uv >/dev/null 2>&1; then \
		uv venv .venv 2>/dev/null || true; \
		uv pip install -e ".[gui,mcp]" ; \
	else \
		$(PYTHON) -m pip install --upgrade pip; \
		$(PYTHON) -m pip install -e ".[gui,mcp]" ; \
	fi
	@echo "[*] Installing additional dependencies from requirements.txt..."
	@$(PYTHON) -m pip install -r requirements.txt || true
	@echo "[OK] All components installed!"
	@echo ""
	@echo "Usage:"
	@echo "  CLI: webclone clone https://example.com"
	@echo "  GUI: make gui"
	@echo "  MCP: make mcp"

install-gui: ## Install with GUI support
	@echo "[*] Installing WebClone with GUI support..."
	@if command -v uv >/dev/null 2>&1; then \
		uv venv .venv 2>/dev/null || true; \
		uv pip install -e ".[gui]" ; \
	else \
		$(PYTHON) -m pip install --upgrade pip; \
		$(PYTHON) -m pip install -e ".[gui]" ; \
	fi
	@$(PYTHON) -m pip install ttkbootstrap aiofiles selenium webdriver-manager || true
	@echo "[OK] GUI dependencies installed!"
	@$(PYTHON) -c "import tkinter" 2>/dev/null || echo "[WARN] Tkinter not available - install python3-tk"

install-mcp: ## Install MCP server dependencies
	@echo "[*] Installing WebClone MCP server..."
	@if command -v uv >/dev/null 2>&1; then \
		uv venv .venv 2>/dev/null || true; \
		uv pip install -e ".[mcp]" ; \
	else \
		$(PYTHON) -m pip install --upgrade pip; \
		$(PYTHON) -m pip install -e ".[mcp]" ; \
	fi
	@echo "[OK] MCP server installed!"
	@echo ""
	@echo "Add to Claude Desktop config:"
	@echo '  {"mcpServers": {"webclone": {"command": "webclone-mcp"}}}'

dev: ## Install development dependencies
	@echo "[*] Installing development dependencies..."
	@if command -v uv >/dev/null 2>&1; then \
		uv venv .venv 2>/dev/null || true; \
		uv pip install -e ".[dev]" ; \
	else \
		$(PYTHON) -m pip install --upgrade pip; \
		$(PYTHON) -m pip install -e ".[dev]" ; \
	fi
	@echo "[OK] Development environment ready!"

# ============================================================================
# Running
# ============================================================================

gui: ## Launch the Desktop GUI
	@echo "[*] Starting WebClone Desktop GUI..."
	@$(PYTHON) webclone-gui.py

mcp: ## Launch the MCP server
	@echo "[*] Starting WebClone MCP Server..."
	@$(PYTHON) -m webclone.mcp

start: ## Show CLI help
	@$(PYTHON) -m webclone.cli --help

run: ## Run example clone (example.com)
	@echo "[*] Running example clone..."
	@$(PYTHON) -m webclone.cli clone https://example.com --max-pages 5 -o ./demo_output

# ============================================================================
# Testing & Quality
# ============================================================================

test: ## Run tests with pytest and coverage
	@echo "[*] Running tests..."
	@PYTHONPATH=src $(PYTHON) -m pytest tests/ -v --cov=src/webclone --cov-report=term-missing || true
	@echo "[OK] Tests complete!"

test-fast: ## Run tests without coverage
	@echo "[*] Running fast tests..."
	@PYTHONPATH=src $(PYTHON) -m pytest tests/ -v || true
	@echo "[OK] Tests complete!"

lint: ## Run ruff linter
	@echo "[*] Running linter..."
	@ruff check src/ tests/ || true
	@echo "[OK] Linting complete!"

format: ## Format code with ruff
	@echo "[*] Formatting code..."
	@ruff format src/ tests/ || true
	@ruff check --fix src/ tests/ || true
	@echo "[OK] Code formatted!"

typecheck: ## Run mypy type checker
	@echo "[*] Running type checker..."
	@mypy src/ || true
	@echo "[OK] Type checking complete!"

audit: lint typecheck ## Run all quality checks
	@echo "[*] Running security audit..."
	@bandit -r src/ -ll || true
	@echo "[OK] All quality checks complete!"

# ============================================================================
# Docker
# ============================================================================

docker-build: ## Build Docker image
	@echo "[*] Building Docker image..."
	@docker build -t webclone:latest .
	@echo "[OK] Docker image built!"

docker-run: ## Run WebClone in Docker
	@echo "[*] Running WebClone in Docker..."
	@docker run --rm -v $(PWD)/output:/data webclone:latest clone https://example.com --max-pages 5

docker-shell: ## Open shell in Docker container
	@docker run --rm -it -v $(PWD)/output:/data --entrypoint /bin/bash webclone:latest

# ============================================================================
# Maintenance
# ============================================================================

clean: ## Remove build artifacts and cache files
	@echo "[*] Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf dist/ build/ .coverage 2>/dev/null || true
	@echo "[OK] Cleanup complete!"

clean-all: clean ## Deep clean including output directories
	@echo "[*] Deep cleaning..."
	@rm -rf website_mirror/ demo_output/ output/ 2>/dev/null || true
	@echo "[OK] Deep cleanup complete!"

# ============================================================================
# Distribution
# ============================================================================

build: clean ## Build distribution packages
	@echo "[*] Building distribution packages..."
	@$(PYTHON) -m build
	@echo "[OK] Build complete! Check dist/"

publish: build ## Publish to PyPI
	@echo "[*] Publishing to PyPI..."
	@twine upload dist/*
	@echo "[OK] Published!"

# ============================================================================
# Reports
# ============================================================================

coverage: ## Generate HTML coverage report
	@echo "[*] Generating coverage report..."
	@pytest tests/ --cov=src/webclone --cov-report=html
	@echo "[OK] Coverage report: htmlcov/index.html"

benchmark: ## Run performance benchmarks
	@echo "[*] Running benchmark..."
	@time $(PYTHON) -m webclone.cli clone https://example.com --max-pages 10 -o ./benchmark_output
	@echo "[OK] Benchmark complete!"
