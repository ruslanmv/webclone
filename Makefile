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

.PHONY: help uv-ensure install install-all dev start run \
        install-gui gui gui-dev \
        install-mcp mcp mcp-dev \
        test test-fast lint format typecheck audit \
        clean clean-all \
        docker-build docker-run docker-shell \
        build publish coverage benchmark

# ANSI color codes for beautiful output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Default target - show help
.DEFAULT_GOAL := help

help: ## Display this help message
	@echo "$(BLUE)╔═══════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║$(NC)  $(GREEN)WebClone - A Blazingly Fast Website Cloning Engine$(NC)      $(BLUE)║$(NC)"
	@echo "$(BLUE)╚═══════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(YELLOW)Available commands:$(NC)"
	@echo ""
	@awk 'BEGIN { \
		FS = ":.*##"; \
		print ""; \
	} \
	/^[a-zA-Z_-]+:.*##/ { \
		sub(":", "", $$1); \
		printf "  $(GREEN)%-18s$(NC) %s\n", $$1, $$2; \
	} \
	/^##@/ { \
		printf "\n$(YELLOW)%s$(NC)\n", substr($$0, 5); \
	}' $(MAKEFILE_LIST)
	@echo ""

# Internal: ensure uv exists and a .venv is created
uv-ensure:
	@echo "$(BLUE)🔍 Checking uv and virtual environment...$(NC)"
	command -v uv >/dev/null 2>&1 || { echo "$(RED)Error: uv is not installed. Visit https://github.com/astral-sh/uv$(NC)"; exit 1; }
	test -d ".venv" || (echo "$(BLUE)🐍 Creating virtual environment with uv in .venv...$(NC)" && uv venv .venv)

##@ 🚀 Development

install: uv-ensure ## Install production dependencies using uv (CLI only)
	@echo "$(BLUE)📦 Installing production dependencies with uv...$(NC)"
	uv pip install -e .
	@echo "$(GREEN)✓ Installation complete!$(NC)"

install-all: uv-ensure ## Install CLI + GUI + MCP (all-in-one)
	@echo "$(BLUE)📦 Installing WebClone CLI + GUI + MCP...$(NC)"
	uv pip install -e ".[gui,mcp]"
	@echo "$(GREEN)✓ All WebClone components installed!$(NC)"
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
	@echo "$(BLUE)🚀 Starting WebClone...$(NC)"
	python -m webclone.cli --help

run: ## Quick clone example (example.com)
	@echo "$(BLUE)🌐 Running example clone...$(NC)"
	python -m webclone.cli clone https://example.com --max-pages 5 -o ./demo_output

##@ 🎨 GUI Interface

install-gui: uv-ensure ## Install with GUI dependencies
	@echo "$(BLUE)📦 Installing WebClone with GUI support...$(NC)"
	uv pip install -e ".[gui]"
	@echo "$(GREEN)✓ GUI dependencies installed!$(NC)"

gui: ## Launch the Enterprise Desktop GUI
	@echo "$(BLUE)🎨 Starting WebClone Enterprise Desktop GUI...$(NC)"
	python webclone-gui.py

gui-dev: uv-ensure ## Launch GUI with dev dependencies
	@echo "$(BLUE)🎨 Starting WebClone GUI (dev mode)...$(NC)"
	uv pip install -e ".[gui,dev]"
	python webclone-gui.py

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
	python -m webclone.mcp

mcp-dev: uv-ensure ## Install MCP with dev dependencies
	@echo "$(BLUE)🤖 Installing MCP server with dev tools...$(NC)"
	uv pip install -e ".[mcp,dev]"
	@echo "$(GREEN)✓ MCP development environment ready!$(NC)"

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
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
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
	python -m build
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
	time python -m webclone.cli clone https://example.com --max-pages 10 -o ./benchmark_output
	@echo "$(GREEN)✓ Benchmark complete!$(NC)"
