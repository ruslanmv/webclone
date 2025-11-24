# 🔐 Authentication & Anti-Bot Detection Guide

This guide explains how WebMirror handles authentication challenges and bypasses bot detection systems.

## 🎯 Problem Overview

Modern websites (especially Google, Facebook, LinkedIn, etc.) employ sophisticated bot detection:

- **"This browser or app may not be secure"** - Google's automated browser detection
- **GCM/FCM Errors** - Google Cloud Messaging registration failures
- **Rate Limiting** - Too many requests from the same IP
- **CAPTCHA Challenges** - Human verification systems

WebMirror includes multiple strategies to handle these challenges.

---

## ✨ Built-in Stealth Features

WebMirror automatically enables stealth mode when you use the Selenium service:

### 🛡️ What's Included

1. **Navigator.webdriver Masking** - Removes the automation flag
2. **Plugin Spoofing** - Makes browser appear to have plugins
3. **Cloud Services Disabled** - Prevents GCM/FCM errors
4. **Human-like User Agent** - Uses realistic browser signatures
5. **Automation Detection Disabled** - Removes Selenium markers

### 📋 Automatic Fixes

```python
from webmirror.services import SeleniumService
from webmirror.models.config import SeleniumConfig

# Stealth mode is enabled by default!
config = SeleniumConfig(headless=False)  # Set False to see browser
service = SeleniumService(config)
service.start_driver()

# The browser now appears as a regular Chrome instance
service.navigate_to("https://google.com")
```

---

## 🚀 Method 1: Cookie-Based Authentication

**Best for**: Sites requiring login credentials

### Step 1: Manual Login & Save Cookies

```python
from pathlib import Path
from webmirror.services import SeleniumService
from webmirror.models.config import SeleniumConfig

# Create service with visible browser
config = SeleniumConfig(headless=False)
service = SeleniumService(config)
service.start_driver()

# Open login page and wait for manual authentication
service.manual_login_session(
    start_url="https://accounts.google.com",
    cookie_save_path=Path("./cookies/google_session.json")
)
# ↑ Browser opens, you log in manually, press Enter when done
```

### Step 2: Reuse Cookies for Automation

```python
from pathlib import Path
from webmirror.services import SeleniumService
from webmirror.models.config import SeleniumConfig

config = SeleniumConfig(headless=True)  # Now can be headless!
service = SeleniumService(config)
service.start_driver()

# Load saved authentication
service.navigate_to("https://google.com")  # Must visit domain first
service.load_cookies(Path("./cookies/google_session.json"))
service.navigate_to("https://accounts.google.com")  # Now authenticated!

# Proceed with scraping
```

---

## 🔧 Method 2: Automatic Block Detection

WebMirror can detect and attempt to bypass authentication blocks:

```python
from webmirror.services import SeleniumService
from webmirror.models.config import SeleniumConfig

config = SeleniumConfig(headless=False)
service = SeleniumService(config)
service.start_driver()
service.navigate_to("https://protected-site.com")

# Automatically detect and handle blocks
if service.handle_authentication_block():
    print("Block detected and handled!")
else:
    print("No blocks detected, proceeding normally")
```

### What It Does

1. **Detects** common block messages
2. **Simulates** human behavior (mouse movements, scrolling)
3. **Clears** browser data and retries
4. **Reports** if manual intervention is needed

---

## ⚡ Method 3: Rate Limit Detection

Check if you're being rate-limited:

```python
service.navigate_to("https://api-endpoint.com")

if service.check_rate_limit():
    print("Rate limited! Increase delay_ms in config")
    # Implement backoff strategy
    import time
    time.sleep(60)  # Wait 1 minute
```

---

## 🎭 Method 4: Using Residential Proxies

For maximum stealth, combine WebMirror with residential proxies:

```python
from selenium.webdriver.chrome.options import Options
from webmirror.models.config import SeleniumConfig

config = SeleniumConfig(headless=True)
service = SeleniumService(config)

# Before starting, add proxy to Chrome options
# (You'll need to modify start_driver() to accept custom options)
chrome_options = Options()
chrome_options.add_argument('--proxy-server=http://proxy-ip:port')

# Then use normally
service.start_driver()
```

---

## 🔍 Fixing Specific Errors

### Error: "Couldn't sign you in - This browser or app may not be secure"

**Solution**: Use cookie-based authentication (Method 1)

```bash
# 1. Run interactive login
python -c "
from webmirror.services import SeleniumService
from webmirror.models.config import SeleniumConfig
from pathlib import Path

service = SeleniumService(SeleniumConfig(headless=False))
service.start_driver()
service.manual_login_session('https://accounts.google.com', Path('cookies/google.json'))
"

# 2. Use saved cookies in your scripts
```

### Error: GCM/FCM Registration Errors

**Solution**: Already fixed! WebMirror disables these services:

```
✅ --disable-features=GoogleServices
✅ --disable-cloud-print
✅ --disable-sync
✅ --no-service-autorun
```

These arguments are automatically applied.

### Error: Rate Limiting (429 Too Many Requests)

**Solution**: Increase delays in configuration

```python
from webmirror.models.config import CrawlConfig

config = CrawlConfig(
    start_url="https://example.com",
    delay_ms=2000,  # 2 second delay between requests
    workers=2,       # Reduce concurrent workers
)
```

---

## 💡 Best Practices

### 1. **Start with Headless=False**

See what the browser sees:
```python
config = SeleniumConfig(headless=False)
```

### 2. **Save Cookies Early**

Authenticate once, reuse forever:
```python
service.save_cookies(Path("./cookies/session.json"))
```

### 3. **Respect Rate Limits**

```python
config = CrawlConfig(delay_ms=1000, workers=3)
```

### 4. **Use Realistic User Agents**

```python
config = SeleniumConfig(
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
)
```

### 5. **Monitor for Blocks**

```python
if service.handle_authentication_block():
    # Take action - maybe switch IP or pause
    time.sleep(300)  # 5 minute cooldown
```

---

## 🎓 Advanced: Custom Stealth Scripts

Inject custom JavaScript to further mask automation:

```python
service.driver.execute_cdp_cmd(
    "Page.addScriptToEvaluateOnNewDocument",
    {
        "source": """
        // Your custom stealth code
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8
        });
        """
    }
)
```

---

## 📊 Success Checklist

- [ ] GCM/FCM errors eliminated
- [ ] No "insecure browser" warnings
- [ ] Successfully logged in and saved cookies
- [ ] Rate limits respected (check logs)
- [ ] Headless mode working with authentication

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| Still getting blocked | Try Method 1 (cookie auth) |
| GCM errors persist | Update Chrome/ChromeDriver to latest |
| Rate limited | Increase `delay_ms`, reduce `workers` |
| CAPTCHA appears | Use cookie auth after manual solving |
| Cookies not working | Check domain matches, try refreshing |

---

## 🔗 Related Documentation

- [Configuration Guide](./CONFIGURATION.md)
- [CLI Usage](../README.md#usage)
- [Docker Deployment](../README.md#docker)

---

**Author**: Ruslan Magana
**Website**: [ruslanmv.com](https://ruslanmv.com)

Need help? Open an issue on [GitHub](https://github.com/ruslanmv/webmirror/issues)!
