# 🚀 WebClone Quick Reference Card

## Common Commands

```bash
# Basic clone
webclone clone https://example.com

# With authentication examples
python examples/authenticated_crawl.py

# Custom output and workers
webclone clone https://example.com -o ./output --workers 10

# Limit pages
webclone clone https://example.com --max-pages 100

# Deep crawl
webclone clone https://example.com --max-depth 5 --recursive
```

## Authentication Fixes

### Problem: "Browser may not be secure"

**Solution 1: Cookie Auth (Recommended)**
```python
# Step 1: Manual login (run once)
from webclone.services import SeleniumService
from webclone.models.config import SeleniumConfig
from pathlib import Path

service = SeleniumService(SeleniumConfig(headless=False))
service.start_driver()
service.manual_login_session(
    "https://accounts.google.com",
    Path("cookies/google.json")
)

# Step 2: Use saved cookies (automated)
service = SeleniumService(SeleniumConfig(headless=True))
service.start_driver()
service.navigate_to("https://google.com")
service.load_cookies(Path("cookies/google.json"))
# ✅ Now authenticated!
```

**Solution 2: Automatic Detection**
```python
service.navigate_to("https://protected-site.com")
if service.handle_authentication_block():
    print("Block handled automatically")
```

### Problem: GCM/FCM Errors

✅ **Already Fixed!** The following flags are automatically applied:
- `--disable-features=GoogleServices`
- `--disable-cloud-print`
- `--disable-sync`
- `--no-service-autorun`

No action needed - errors eliminated by default.

### Problem: Rate Limiting

```python
# Check for rate limits
if service.check_rate_limit():
    print("Rate limited - increase delay")
    time.sleep(60)

# Or configure delays upfront
config = CrawlConfig(
    start_url="https://example.com",
    delay_ms=2000,  # 2 seconds
    workers=3       # Fewer workers
)
```

## Configuration

### Environment Variables

```bash
# Create .env file
cp .env.example .env

# Edit as needed
WEBCLONE_SELENIUM_HEADLESS=true
WEBCLONE_SELENIUM_TIMEOUT=30
WEBCLONE_MAX_PAGES=100
WEBCLONE_WORKERS=5
```

### Python Configuration

```python
from webclone.models.config import CrawlConfig, SeleniumConfig

# Crawler config
crawl_config = CrawlConfig(
    start_url="https://example.com",
    output_dir=Path("./output"),
    recursive=True,
    max_depth=3,
    max_pages=100,
    workers=10,
    delay_ms=1000,
    save_pdf=True,
    include_assets=True,
)

# Selenium config
selenium_config = SeleniumConfig(
    headless=True,
    window_size="1920,1080",
    timeout=30,
    user_agent="Mozilla/5.0...",
)
```

## Makefile Commands

```bash
make install      # Install with uv
make dev          # Install dev dependencies
make test         # Run tests
make lint         # Run linter
make format       # Format code
make audit        # Run all quality checks
make docker-build # Build Docker image
make clean        # Clean build artifacts
```

## Troubleshooting

| Error | Fix |
|-------|-----|
| Import errors | `make install` |
| Chrome not found | Install Chrome/Chromium |
| Authentication blocks | Use cookie auth (see above) |
| GCM/FCM errors | Already fixed - update to latest |
| Rate limited | Increase `delay_ms` in config |
| Cookies not working | Ensure domain matches, refresh cookies |

## Advanced Usage

### Custom Stealth JavaScript

```python
service.driver.execute_cdp_cmd(
    "Page.addScriptToEvaluateOnNewDocument",
    {"source": "// Your custom code"}
)
```

### Manual Cookie Management

```python
# Save cookies
service.save_cookies(Path("./cookies/session.json"))

# Load cookies
service.load_cookies(Path("./cookies/session.json"))
```

### Human Behavior Simulation

```python
# Automatically simulated during authentication
service._simulate_human_behavior()
```

## Documentation

- 📖 [Full README](../README.md)
- 🔐 [Authentication Guide](./AUTHENTICATION_GUIDE.md)
- 💡 [Examples](../examples/README.md)
- 🤝 [Contributing](../CONTRIBUTING.md)

## Support

- 🐛 Issues: https://github.com/ruslanmv/webclone/issues
- 📧 Email: contact@ruslanmv.com
- 🌐 Website: ruslanmv.com

---

**Author**: Ruslan Magana | **License**: Apache 2.0
