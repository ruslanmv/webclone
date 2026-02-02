# WebClone

<div align="center">

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)

**Fast, async website cloning engine with Cloudflare bypass**

</div>

---

## Features

| Feature | Description |
|---------|-------------|
| **Fast Async Engine** | Concurrent downloads with 5-50 parallel workers |
| **Cloudflare Bypass** | Handle bot detection and challenge pages |
| **Dynamic Rendering** | Selenium for JavaScript-heavy sites |
| **Authentication** | Cookie-based sessions, stealth mode |
| **Multiple Interfaces** | CLI, Desktop GUI, Python API, MCP Server |

---

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/ruslanmv/webclone.git
cd webclone

# Install all dependencies
make install

# Verify installation
make test
```

### Basic Usage

```bash
# Clone a website
webclone clone https://example.com

# With options
webclone clone https://example.com --output ./mirror --workers 10 --max-pages 50
```

### Desktop GUI

```bash
make install-gui
make gui
```

---

## Cloudflare Bypass

For sites with Cloudflare protection (403 errors):

```python
from webclone.models.config import SeleniumConfig
from webclone.services.selenium_service import SeleniumService

config = SeleniumConfig(headless=False)
service = SeleniumService(config)
service.start_driver()

# Navigate with automatic Cloudflare handling
success = service.navigate_with_cloudflare_bypass("https://protected-site.com")

if success:
    service.save_cookies("cookies/session.json")

service.stop_driver()
```

---

## CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output, -o` | Output directory | `website_mirror` |
| `--workers, -w` | Concurrent workers | `5` |
| `--max-pages` | Max pages to crawl | `0` (unlimited) |
| `--max-depth` | Max crawl depth | `0` (unlimited) |
| `--delay` | Delay between requests (ms) | `100` |
| `--no-assets` | Skip CSS, JS, images | `false` |
| `--recursive` | Follow links | `true` |

---

## Make Commands

| Command | Description |
|---------|-------------|
| `make install` | Install production dependencies |
| `make install-all` | Install CLI + GUI + MCP |
| `make test` | Run tests with coverage |
| `make gui` | Launch Desktop GUI |
| `make clean` | Remove cache files |

---

## Project Structure

```
webclone/
├── src/webclone/
│   ├── cli.py                 # Command line interface
│   ├── core/
│   │   ├── crawler.py         # Async crawler
│   │   └── downloader.py      # Asset downloader
│   ├── services/
│   │   ├── selenium_service.py    # Browser automation
│   │   └── cloudflare_bypass.py   # Cloudflare handling
│   └── models/
│       └── config.py          # Configuration
├── examples/
│   └── cloudflare_bypass_example.py
└── tests/
```

---

## Requirements

- Python 3.11+
- Chrome/Chromium (for Selenium)

---

## License

Apache 2.0 - See [LICENSE](LICENSE)

---

## Author

**Ruslan Magana** - [ruslanmv.com](https://ruslanmv.com)
