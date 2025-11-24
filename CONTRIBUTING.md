# Contributing to WebClone

First off, thank you for considering contributing to WebClone! 🎉

This document provides guidelines for contributing to the project. Following these guidelines helps maintain code quality and makes the contribution process smooth for everyone.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Reporting Bugs](#reporting-bugs)
- [Feature Requests](#feature-requests)

## 🤝 Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please be respectful and professional in all interactions.

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended)
- Git
- Chrome/Chromium browser (for Selenium tests)

### Setup Development Environment

```bash
# 1. Fork the repository on GitHub
# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/webclone.git
cd webclone

# 3. Add upstream remote
git remote add upstream https://github.com/ruslanmv/webclone.git

# 4. Install development dependencies
make dev

# 5. Verify installation
make test
```

## 🔄 Development Workflow

### Creating a Feature Branch

```bash
# Update your main branch
git checkout main
git pull upstream main

# Create a feature branch
git checkout -b feature/your-feature-name
```

### Making Changes

1. **Write code** following our [coding standards](#coding-standards)
2. **Add tests** for new functionality
3. **Update documentation** if needed
4. **Run quality checks**:
   ```bash
   make audit  # Runs linting, type checking, and security scans
   make test   # Runs test suite
   ```

### Committing Changes

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

```bash
# Format: <type>(<scope>): <description>

git commit -m "feat(crawler): add support for custom headers"
git commit -m "fix(cli): handle keyboard interrupt gracefully"
git commit -m "docs: update installation instructions"
git commit -m "test: add tests for asset downloader"
```

**Commit Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Maintenance tasks

## 📝 Coding Standards

### Python Style Guide

WebClone follows strict coding standards enforced by automated tools:

1. **Formatting**: Use `ruff format`
   ```bash
   make format
   ```

2. **Linting**: Use `ruff check`
   ```bash
   make lint
   ```

3. **Type Checking**: Use `mypy`
   ```bash
   make typecheck
   ```

### Code Quality Requirements

- ✅ **100% type coverage**: All functions must have type hints
- ✅ **90%+ test coverage**: Critical paths must be tested
- ✅ **No linting errors**: Code must pass `ruff check`
- ✅ **No type errors**: Code must pass `mypy`
- ✅ **No security issues**: Code must pass `bandit` scan

### Style Conventions

```python
# ✅ Good: Type hints, docstrings, async/await
async def download_asset(url: str, timeout: int = 30) -> Optional[bytes]:
    """Download an asset from the given URL.

    Args:
        url: The URL to download from
        timeout: Timeout in seconds

    Returns:
        Downloaded bytes or None if failed

    Raises:
        aiohttp.ClientError: If download fails
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=timeout) as response:
            return await response.read()

# ❌ Bad: No types, no docstring, blocking I/O
def download_asset(url, timeout=30):
    response = requests.get(url)
    return response.content
```

### Documentation Style

We use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """Short description.

    Longer description if needed. This can span
    multiple lines and include details.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When something goes wrong
        TypeError: When type is incorrect

    Examples:
        >>> function_name("test", 42)
        True
    """
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_models.py

# Run with verbose output
pytest tests/ -v

# Run with coverage report
make coverage
```

### Writing Tests

- Place tests in the `tests/` directory
- Mirror the source structure (e.g., `tests/test_crawler.py` for `src/webclone/core/crawler.py`)
- Use descriptive test names: `test_download_asset_with_invalid_url`
- Use pytest fixtures for common setup
- Mock external dependencies (network calls, file I/O)

Example:

```python
import pytest
from webclone.core.downloader import AssetDownloader

class TestAssetDownloader:
    """Tests for AssetDownloader class."""

    @pytest.fixture
    def downloader(self, tmp_path):
        """Create a downloader instance for testing."""
        config = CrawlConfig(
            start_url="https://example.com",
            output_dir=tmp_path
        )
        return AssetDownloader(config)

    async def test_download_asset_success(self, downloader, aiohttp_mock):
        """Test successful asset download."""
        aiohttp_mock.get("https://example.com/style.css", status=200, body=b"body{}")

        result = await downloader.download_asset("https://example.com/style.css")

        assert result is not None
        assert result.status_code == 200
```

## 📤 Submitting Changes

### Pull Request Process

1. **Update your branch** with latest upstream changes:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create Pull Request** on GitHub with:
   - Clear title following conventional commits format
   - Description of changes and motivation
   - Reference to related issues (e.g., "Closes #123")
   - Screenshots for UI changes

4. **Wait for review** and address feedback

### Pull Request Checklist

Before submitting, ensure:

- [ ] Code follows style guidelines (`make audit` passes)
- [ ] Tests pass (`make test` passes)
- [ ] New code has tests
- [ ] Documentation is updated
- [ ] Commit messages follow conventional commits
- [ ] Branch is up to date with main

## 🐛 Reporting Bugs

### Before Reporting

- Check existing issues to avoid duplicates
- Test with the latest version
- Collect reproduction steps

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce:
1. Run command '...'
2. See error

**Expected behavior**
What you expected to happen.

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.11.5]
- WebClone version: [e.g., 1.0.0]

**Additional context**
Any other relevant information.
```

## 💡 Feature Requests

We love new ideas! To request a feature:

1. **Check existing issues** for similar requests
2. **Open a new issue** with the `enhancement` label
3. **Describe the feature** and its use case
4. **Explain why** it would be valuable

### Feature Request Template

```markdown
**Is your feature related to a problem?**
Describe the problem you're trying to solve.

**Describe the solution**
What you want to happen.

**Alternatives considered**
Other solutions you've considered.

**Additional context**
Any other relevant information.
```

## 📞 Getting Help

- 💬 **Discussions**: Use GitHub Discussions for questions
- 📧 **Email**: contact@ruslanmv.com
- 🐛 **Issues**: Use GitHub Issues for bugs

## 🙏 Recognition

Contributors will be:
- Listed in the project's contributors section
- Mentioned in release notes for significant contributions
- Given credit in documentation

Thank you for contributing to WebClone! 🚀

---

**Author**: Ruslan Magana
**Website**: [ruslanmv.com](https://ruslanmv.com)
