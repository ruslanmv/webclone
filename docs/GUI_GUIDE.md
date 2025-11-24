# 🎨 WebMirror GUI User Guide

## Overview

WebMirror's Professional Web GUI provides a beautiful, intuitive interface for website cloning and archival. No command-line experience required!

---

## 🚀 Quick Start

### Installation

```bash
# Clone or navigate to WebMirror directory
cd webmirror

# Install with GUI support
make install-gui
```

### Launch

```bash
# Start the GUI
make gui
```

The GUI will automatically open in your default browser at `http://localhost:8501`

---

## 📖 Interface Guide

### 1. 🏠 Home Dashboard

The home page provides:
- **Feature Overview** - Key capabilities at a glance
- **Quick Start Guide** - Step-by-step instructions
- **System Status** - Current configuration and resources

**Use Case:** First-time users should start here to understand the workflow.

---

### 2. 🔐 Authentication Manager

#### Why Authenticate?

Many websites require login or block automated access. The Authentication Manager helps you:
- Log in to protected sites
- Save your session cookies
- Reuse authentication for future crawls

#### Workflow

**Tab 1: New Login**

1. **Enter Login URL**
   - Example: `https://accounts.google.com`
   - Or any site requiring authentication

2. **Set Session Name**
   - Give it a memorable name (e.g., `google_work`, `facebook_personal`)
   - This helps organize multiple accounts

3. **Click "Open Browser for Login"**
   - A real Chrome browser window opens
   - You see the login page

4. **Manual Login**
   - Log in normally (username, password, 2FA, etc.)
   - Navigate to your target page
   - Complete any security checks

5. **Click "Save Session & Cookies"**
   - Your authenticated session is saved
   - Browser closes automatically
   - Cookies stored in `./cookies/[session_name].json`

**Tab 2: Load Cookies**

- View all saved sessions
- Select one to reuse
- Preview cookie details
- One-click loading for future crawls

**Tab 3: Help**

- Detailed authentication guide
- Troubleshooting tips
- Security best practices

#### Supported Sites

- ✅ Google (Gmail, Drive, Docs, etc.)
- ✅ Facebook
- ✅ LinkedIn
- ✅ Twitter/X
- ✅ GitHub (private repos)
- ✅ Any site with cookie-based auth

---

### 3. 📥 Crawl Website

The main interface for configuring and running crawls.

#### Target Configuration

**Website URL**
- The starting point for your crawl
- Must be a valid HTTP/HTTPS URL
- Example: `https://example.com`

**Output Directory**
- Where files will be saved
- Default: `./website_mirror`
- Will create subdirectories: `pages/`, `assets/`, `pdfs/`, `reports/`

#### Advanced Settings (Expandable)

**Crawling Options:**

| Setting | Description | Recommended |
|---------|-------------|-------------|
| **Recursive Crawl** | Follow links to other pages | ✅ Enabled |
| **Max Depth** | How deep to follow links (0 = unlimited) | 0 (unlimited) |
| **Max Pages** | Maximum pages to download (0 = unlimited) | 0 (unlimited) |
| **Same Domain Only** | Only crawl URLs on the same domain | ✅ Enabled |

**Performance Options:**

| Setting | Range | Description | Recommended |
|---------|-------|-------------|-------------|
| **Workers** | 1-50 | Concurrent downloads | 5-10 |
| **Delay (ms)** | 0-5000 | Pause between requests | 100-1000 |

**Content Options:**

- **Include Assets**: Download CSS, JS, images, fonts
- **Generate PDFs**: Create PDF snapshots of pages

#### Starting a Crawl

1. Configure all settings
2. Load authentication (if needed) from sidebar
3. Click **"▶️ Start Crawl"**
4. Watch real-time progress
5. View results when complete

#### Progress Indicators

During crawl:
- 🟢 **Green status** - Crawling in progress
- 📊 **Progress bar** - Percentage complete
- 🔢 **Live counters** - Pages, assets, size
- ⏱️ **Timer** - Elapsed time

---

### 4. 📊 Results & Analytics

View detailed statistics and download reports.

#### Summary Cards

- **Pages Crawled** - Total HTML pages downloaded
- **Assets Downloaded** - CSS, JS, images, etc.
- **Total Size** - Combined size in MB
- **Duration** - Total crawl time

#### Detailed Tabs

**📄 Pages Tab**

- List of all crawled pages
- URL, title, status code
- Depth, links found, assets
- Expandable for details

**📦 Assets Tab**

- Grouped by resource type
- Count per category (CSS, JS, images, fonts)
- File sizes and paths

**📈 Analytics Tab**

- Performance metrics
- Average download speed
- Pages per second
- Error summary (if any)

#### Export Options

- Download full results as JSON
- Export metadata to CSV
- Archive all content as ZIP

---

## 💡 Usage Examples

### Example 1: Simple Public Website

**Scenario:** Archive a blog for offline reading

```
1. Go to "Crawl Website"
2. URL: https://myblog.com
3. Settings:
   - Recursive: ✅
   - Max Depth: 3
   - Workers: 10
4. Click "Start Crawl"
5. Wait for completion
6. Check "Results" tab
```

### Example 2: Authenticated Site

**Scenario:** Download your Google Drive documents

```
1. Go to "Authentication"
2. Login URL: https://accounts.google.com
3. Session Name: google_drive
4. Click "Open Browser"
5. Log in to Google
6. Navigate to Drive
7. Click "Save Session"
8. Go to "Crawl Website"
9. URL: https://drive.google.com/drive/folders/[your_folder_id]
10. Verify "Using session: google_drive" shows in sidebar
11. Click "Start Crawl"
```

### Example 3: Large Site with Rate Limiting

**Scenario:** Clone a documentation site without getting blocked

```
1. Go to "Crawl Website"
2. URL: https://docs.example.com
3. Advanced Settings:
   - Max Pages: 200 (limit scope)
   - Workers: 3 (be gentle)
   - Delay: 2000ms (2 seconds between requests)
4. Click "Start Crawl"
5. Monitor for rate limit warnings in logs
```

---

## ⚙️ Configuration

### Environment Variables

Create `.env` file in project root:

```bash
# Selenium Configuration
WEBMIRROR_SELENIUM_HEADLESS=true
WEBMIRROR_SELENIUM_TIMEOUT=30

# Crawler Configuration
WEBMIRROR_WORKERS=5
WEBMIRROR_DELAY_MS=100
WEBMIRROR_MAX_PAGES=0
```

### Cookie Storage

Cookies are stored in `./cookies/` directory:
- Each session = one JSON file
- Contains domain, name, value, expiry
- **Never share cookie files** (contain auth tokens)

---

## 🐛 Troubleshooting

### GUI Won't Start

**Problem:** `streamlit: command not found`

**Solution:**
```bash
make install-gui
```

### Browser Won't Open for Auth

**Problem:** "Chrome not found"

**Solution:**
- Install Chrome or Chromium
- Update WebDriver: `pip install --upgrade webdriver-manager`

### Cookies Not Working

**Problem:** Still getting "Login required"

**Solutions:**
1. Session expired - Re-authenticate
2. Domain mismatch - Check cookie file
3. 2FA required - Complete in manual login
4. IP change - Some sites invalidate cookies on IP change

### Slow Crawling

**Problem:** Taking too long

**Solutions:**
1. Increase workers (try 10-20)
2. Reduce delay_ms (try 50-100)
3. Set max_pages limit (try 100)
4. Disable PDF generation

### Memory Issues

**Problem:** GUI crashes or freezes

**Solutions:**
1. Reduce workers (try 3-5)
2. Increase delay_ms (try 1000+)
3. Set max_pages limit
4. Close other applications

---

## 🔒 Security & Privacy

### Cookie Security

- **Storage**: Cookies stored locally in plain JSON
- **Access**: Only you have access to cookie files
- **Transmission**: Never sent to WebMirror servers (no servers exist!)
- **Expiry**: Cookies expire per site's policy

### Best Practices

1. **Don't share cookie files** - They contain auth tokens
2. **Rotate sessions** - Re-authenticate periodically
3. **Use specific accounts** - Create dedicated accounts for scraping
4. **Check Terms of Service** - Ensure scraping is allowed
5. **Respect robots.txt** - Set appropriate delays

---

## 📞 Support

### Getting Help

- 📖 **Documentation**: `docs/` directory
- 💬 **GitHub Issues**: https://github.com/ruslanmv/webmirror/issues
- 📧 **Email**: contact@ruslanmv.com
- 🌐 **Website**: ruslanmv.com

### Reporting Bugs

When reporting issues, include:
1. WebMirror version
2. Python version
3. Operating system
4. Error messages
5. Steps to reproduce

---

## 🎓 Tips & Tricks

### Performance Optimization

1. **Start small** - Test with max_pages=10 first
2. **Tune workers** - More isn't always better (try 5-10)
3. **Use delays** - Prevent rate limiting (100-1000ms)
4. **Same domain only** - Avoid downloading external assets

### Authentication Tips

1. **Save multiple sessions** - One per site/account
2. **Use descriptive names** - `google_work` vs `google_personal`
3. **Test cookies** - Load and try a small crawl first
4. **Refresh periodically** - Sessions expire (1 day to 30 days typical)

### Content Selection

- **HTML only**: Disable "Include Assets" for text-only archival
- **Full clone**: Enable all options for complete mirror
- **Selective**: Use max_depth to limit scope

---

**Author**: Ruslan Magana
**Website**: [ruslanmv.com](https://ruslanmv.com)
**License**: Apache 2.0

---

*Happy Crawling! 🚀*
