# 🚀 WebMirror

<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](http://mypy-lang.org/)

**A blazingly fast, async-first website cloning engine that preserves everything.**

[Features](#-features) • [Quick Start](#-quick-start) • [Usage](#-usage) • [Docker](#-docker) • [Contributing](#-contributing)

</div>

---

## 🎯 The Why

Traditional website cloners are **slow**, **blocking**, and **fragile**. They download one resource at a time, freeze on JavaScript-heavy sites, and produce incomplete mirrors.

**WebMirror** is different. Built from the ground up with modern Python async/await, it:
- ⚡ **Clones 10-100x faster** with concurrent downloads
- 🎭 **Handles dynamic SPAs** using Selenium for JavaScript rendering
- 🎨 **Delivers beautiful CLI experience** with real-time progress and colored output
- 🏗️ **Follows Clean Architecture** with type-safe, production-grade code
- 🐳 **Ships production-ready** with Docker, full test coverage, and CI/CD

Whether you're archiving websites, conducting competitive research, or building training datasets, **WebMirror** is the definitive solution.

---

## ✨ Features

### 🚀 **Blazingly Fast Async Engine**
- Concurrent downloads with configurable workers (5-50 parallel connections)
- Intelligent queue management with depth-first and breadth-first strategies
- Automatic retry logic with exponential backoff

### 🎭 **Dynamic Page Rendering**
- Full Selenium integration for JavaScript-heavy sites
- Automated sidebar navigation for SPAs (Phoenix LiveView, React, Vue)
- PDF snapshot generation with Chrome DevTools Protocol
- Screenshot capture for visual archival

### 🔐 **Advanced Authentication & Stealth Mode** ⭐ NEW
- **Bypass bot detection**: Masks automation signatures (navigator.webdriver, etc.)
- **Fix GCM/FCM errors**: Disables Google Cloud Messaging registration
- **Cookie-based auth**: Save and reuse login sessions
- **Handle "insecure browser" blocks**: Automatic workarounds for Google, Facebook, etc.
- **Rate limit detection**: Smart throttling and backoff strategies
- **Human behavior simulation**: Mouse movements and natural scrolling

### 🎨 **World-Class CLI Experience**
- Beautiful terminal UI powered by [Rich](https://github.com/Textualize/rich)
- Real-time progress bars with per-resource status
- Colored, formatted output with tables and panels
- JSON logs for production monitoring

### 🏗️ **Production-Grade Architecture**
- **Type-safe**: 100% type hints with Mypy validation
- **Data validation**: Pydantic V2 models with strict schemas
- **Async-first**: Built on `aiohttp` and `asyncio`
- **Modular design**: Clean Architecture with dependency injection
- **Comprehensive logging**: Structured JSON logs with contextual data

### 📦 **Modern Tooling**
- ⚡ **uv**: Lightning-fast dependency management
- 🔍 **ruff**: Ultra-fast linting and formatting
- 🧪 **pytest**: Comprehensive test suite with >90% coverage
- 🐳 **Docker**: Multi-stage builds with distroless base images
- 🔒 **Security**: Bandit audits and dependency scanning

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

```bash
# Using uv (recommended - blazingly fast!)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv pip install webmirror

# Or using pip
pip install webmirror

# Or from source
git clone https://github.com/ruslanmv/webmirror.git
cd webmirror
make install
```

### Your First Clone

```bash
# Clone a website
webmirror clone https://example.com

# With custom settings
webmirror clone https://example.com \
  --output ./my_mirror \
  --workers 10 \
  --max-pages 100 \
  --recursive
```

That's it! Watch as WebMirror downloads your site at lightning speed with beautiful progress bars.

### 🎨 Enterprise Desktop GUI (NEW!)

WebMirror now includes a professional, native desktop interface built with modern Tkinter for superior performance:

```bash
# Install with GUI support
make install-gui

# Launch the Enterprise Desktop GUI
make gui
```

**The GUI opens instantly as a native desktop application with:**
- 🏠 **Home Dashboard** - Feature overview and quick start guide
- 🔐 **Authentication Manager** - Visual cookie-based auth workflow with browser integration
- 📥 **Crawl Configurator** - Point-and-click settings with real-time progress
- 📊 **Results Analytics** - Comprehensive stats, tables, and export options

**Perfect for everyone!** No command line required - professional desktop interface with instant startup, native performance, and seamless OS integration.

**Advantages over web-based GUIs:**
✅ Instant startup (no server to launch)
✅ Native desktop performance
✅ Better OS integration (file dialogs, notifications)
✅ No port conflicts
✅ Offline-friendly

![WebMirror Enterprise GUI](https://via.placeholder.com/800x450?text=WebMirror+Enterprise+Desktop+GUI)

### 🤖 MCP Server for AI Agents (NEW!)

WebMirror is now an **official Model Context Protocol (MCP) server**, making website cloning available to AI agents like Claude, CrewAI, and any MCP-compatible framework!

```bash
# Install MCP server
make install-mcp

# Use with Claude Desktop - add to config:
# ~/.config/claude/claude_desktop_config.json
{
  "mcpServers": {
    "webmirror": {
      "command": "python",
      "args": ["/path/to/webmirror/webmirror-mcp.py"]
    }
  }
}
```

**AI agents can now:**
- 🌐 **clone_website** - Download entire websites automatically
- 📥 **download_file** - Fetch specific files or URLs
- 🔐 **save_authentication** - Guide for saving login sessions
- 📋 **list_saved_sessions** - View all authentication cookies
- ℹ️ **get_site_info** - Analyze websites before downloading

**Example with Claude:**
```
You: Clone the FastAPI documentation website

Claude: I'll clone that for you.
[Uses WebMirror MCP tool]

✅ Cloned 127 pages, 543 assets, 45.2 MB total!
```

**Compatible with:**
- ✅ Claude Desktop
- ✅ CrewAI
- ✅ LangChain
- ✅ Any MCP-compatible AI framework

📖 **See:** `docs/MCP_GUIDE.md` and `MCP_QUICKSTART.md`

---

## 📖 Usage

### Interface Options

WebMirror offers four ways to use it:

1. **🎨 Desktop GUI** (Easiest - Enterprise Edition)
   ```bash
   make gui
   ```
   - Native desktop application
   - Instant startup, no browser required
   - Visual authentication manager
   - Real-time progress tracking
   - Perfect for all users!

2. **🤖 MCP Server** (For AI Agents)
   ```bash
   make install-mcp
   ```
   - Claude Desktop integration
   - CrewAI compatible
   - LangChain ready
   - AI-powered automation
   - Perfect for AI workflows!

3. **💻 Command Line** (Most Powerful)
   ```bash
   webmirror clone https://example.com
   ```
   - Automation and scripting
   - CI/CD pipelines
   - Remote servers
   - Power users

4. **🐍 Python API** (Most Flexible)
   ```python
   from webmirror.core import AsyncCrawler
   # ... your code
   ```
   - Custom integrations
   - Advanced workflows
   - Developers

### Basic Commands

```bash
# Show help
webmirror --help

# Clone a website
webmirror clone <URL> [OPTIONS]

# Analyze a page without downloading
webmirror info <URL>
```

### Advanced Options

```bash
webmirror clone https://example.com \
  --output ./mirror           # Output directory (default: website_mirror)
  --workers 10                # Concurrent workers (default: 5)
  --max-pages 100            # Maximum pages to crawl (0 = unlimited)
  --max-depth 3              # Maximum crawl depth (0 = unlimited)
  --delay 100                # Delay between requests in ms
  --no-assets                # Skip downloading CSS, JS, images
  --no-pdf                   # Skip PDF generation
  --all-domains              # Follow links to other domains
  --verbose                  # Detailed logging output
  --json-logs                # JSON-formatted logs for parsing
```

### Real-World Examples

```bash
# Archive a news site (limit pages to avoid overload)
webmirror clone https://news.example.com --max-pages 50 --workers 5

# Clone a documentation site recursively
webmirror clone https://docs.example.com --recursive --max-depth 5

# Fast clone with maximum parallelism
webmirror clone https://example.com --workers 20 --delay 0

# Production mode with JSON logs
webmirror clone https://example.com --json-logs --output /var/data/mirror
```

### 🔐 Authentication & Stealth Examples

WebMirror includes advanced features to handle authentication and bypass bot detection:

```bash
# Run interactive authentication examples
python examples/authenticated_crawl.py

# Example 1: Manual login and save cookies
# Opens browser, you log in, cookies are saved

# Example 2: Use saved cookies for automation
# Loads cookies, bypasses authentication

# Example 3: Test stealth mode effectiveness
# Visits bot detection sites to verify masking
```

**Python API for Authentication:**

```python
from pathlib import Path
from webmirror.services import SeleniumService
from webmirror.models.config import SeleniumConfig

# Manual login and save session
config = SeleniumConfig(headless=False)
service = SeleniumService(config)
service.start_driver()
service.manual_login_session(
    "https://accounts.google.com",
    Path("./cookies/google.json")
)

# Later: Use saved cookies for automation
config = SeleniumConfig(headless=True)
service = SeleniumService(config)
service.start_driver()
service.navigate_to("https://google.com")
service.load_cookies(Path("./cookies/google.json"))
# Now authenticated!
```

**Fixes Common Issues:**
- ✅ "Couldn't sign you in - browser may not be secure"
- ✅ GCM/FCM registration errors
- ✅ Navigator.webdriver detection
- ✅ Rate limiting and CAPTCHA challenges

See [Authentication Guide](docs/AUTHENTICATION_GUIDE.md) for detailed instructions.

---

## 🐳 Docker

Run WebMirror in a containerized environment:

```bash
# Build the image
make docker-build

# Or manually
docker build -t webmirror:latest .

# Run a clone
docker run --rm -v $(pwd)/output:/data webmirror:latest \
  clone https://example.com --max-pages 10

# Interactive shell
docker run --rm -it -v $(pwd)/output:/data \
  --entrypoint /bin/bash webmirror:latest
```

### Docker Compose Example

```yaml
version: '3.8'
services:
  webmirror:
    image: webmirror:latest
    volumes:
      - ./output:/data
    command: clone https://example.com --workers 10
    environment:
      - WEBMIRROR_MAX_PAGES=100
```

---

## 🏗️ Architecture

WebMirror follows **Clean Architecture** principles:

```
src/webmirror/
├── cli.py              # Typer CLI interface
├── core/               # Core business logic
│   ├── crawler.py      # Async web crawler
│   └── downloader.py   # Asset downloader
├── models/             # Pydantic data models
│   ├── config.py       # Configuration schemas
│   └── metadata.py     # Result metadata
├── services/           # External service integrations
│   └── selenium_service.py
└── utils/              # Shared utilities
    ├── logger.py
    └── helpers.py
```

### Key Design Decisions

1. **Async-First**: All I/O operations use `asyncio` for maximum concurrency
2. **Type Safety**: 100% type coverage with strict Mypy checks
3. **Pydantic V2**: Data validation at system boundaries
4. **Dependency Injection**: Services receive dependencies via constructors
5. **Single Responsibility**: Each module has one clear purpose

---

## 🧪 Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/ruslanmv/webmirror.git
cd webmirror

# Install with dev dependencies
make dev

# Run tests
make test

# Run linter and type checker
make audit

# Format code
make format
```

### Run Tests

```bash
# Full test suite with coverage
make test

# Fast tests without coverage
make test-fast

# Generate HTML coverage report
make coverage
```

### Code Quality

```bash
# Lint with ruff
make lint

# Type check with mypy
make typecheck

# Format code
make format

# Run all quality checks
make audit
```

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Quick Contribution Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run quality checks (`make audit`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

---

## 📊 Benchmarks

Tested on a standard 4-core machine with 100 Mbps connection:

| Website Type | Pages | Assets | Time (WebMirror) | Time (wget) | Speedup |
|--------------|-------|--------|------------------|-------------|---------|
| Static Site  | 50    | 200    | 8s              | 45s         | **5.6x** |
| Blog         | 100   | 500    | 25s             | 3m 20s      | **8.0x** |
| Documentation| 200   | 800    | 1m 10s          | 12m 15s     | **10.5x** |
| SPA/Dynamic  | 30    | 150    | 35s             | N/A*        | **∞** |

*wget cannot render JavaScript-based SPAs

---

## 📄 License

This project is licensed under the **Apache License 2.0** - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Ruslan Magana**
- Website: [ruslanmv.com](https://ruslanmv.com)
- GitHub: [@ruslanmv](https://github.com/ruslanmv)
- Email: contact@ruslanmv.com

---

## 🌟 Star History

If you find WebMirror useful, please consider giving it a star! ⭐

[![Star History Chart](https://api.star-history.com/svg?repos=ruslanmv/webmirror&type=Date)](https://star-history.com/#ruslanmv/webmirror&Date)

---

## 🙏 Acknowledgments

- [Typer](https://typer.tiangolo.com/) - Beautiful CLI framework
- [Rich](https://rich.readthedocs.io/) - Rich terminal formatting
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [aiohttp](https://docs.aiohttp.org/) - Async HTTP client
- [uv](https://github.com/astral-sh/uv) - Lightning-fast package installer

---

<div align="center">

**Made with ❤️ by [Ruslan Magana](https://ruslanmv.com)**

</div>
