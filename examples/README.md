# 📚 WebMirror Examples

This directory contains practical examples demonstrating WebMirror's capabilities.

## 🚀 Quick Start

```bash
# Run the authenticated crawling example
python examples/authenticated_crawl.py
```

## 📋 Available Examples

### 1. **authenticated_crawl.py**

Comprehensive demonstration of handling authentication challenges:

- **Example 1**: Manual login and save cookies
- **Example 2**: Automated crawling with saved cookies
- **Example 3**: Test stealth mode effectiveness
- **Example 4**: Rate limit detection and handling

**Use Cases**:
- Crawling sites requiring login (Google, Facebook, LinkedIn)
- Bypassing "insecure browser" warnings
- Testing bot detection systems

### Running Individual Examples

```python
from examples.authenticated_crawl import (
    example_1_manual_login_and_save,
    example_2_use_saved_cookies,
    example_3_stealth_mode_test,
    example_4_handle_rate_limiting
)

# Run specific example
example_1_manual_login_and_save()
```

## 🔧 Setup

Ensure WebMirror is installed:

```bash
# From project root
make install

# Or with pip
pip install -e .
```

## 📖 Documentation

For detailed guides, see:
- [Authentication Guide](../docs/AUTHENTICATION_GUIDE.md)
- [Main README](../README.md)

## 💡 Tips

1. **Always test with headless=False first** to see what's happening
2. **Save cookies after manual login** for future automation
3. **Check for rate limiting** if crawling large sites
4. **Use delays** between requests to be respectful

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| Import errors | Run `make install` from project root |
| Chrome not found | Install Chrome or Chromium |
| Cookie auth fails | Re-run Example 1 to refresh cookies |
| Rate limited | Increase delays in your config |

## 📝 Adding Your Own Examples

Feel free to add more examples! Template:

```python
#!/usr/bin/env python3
"""Your example description."""

from webmirror.services import SeleniumService
from webmirror.models.config import SeleniumConfig

def your_example() -> None:
    """Example function with docstring."""
    # Your code here
    pass

if __name__ == "__main__":
    your_example()
```

---

**Author**: Ruslan Magana
**Website**: [ruslanmv.com](https://ruslanmv.com)
