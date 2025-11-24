# 🎨 WebMirror Enterprise Desktop GUI - Complete User Guide

## Overview

WebMirror's Enterprise Desktop GUI provides a professional, native desktop interface for website cloning and archival. Built with modern Tkinter (ttkbootstrap), it offers superior performance, instant startup, and seamless OS integration.

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

The Enterprise Desktop GUI will open immediately as a native application.

---

## 📖 Interface Guide

### Application Layout

The WebMirror Enterprise GUI features:

- **Left Sidebar**: Navigation with 4 main sections
- **Content Area**: Dynamic pages with forms, controls, and results
- **Modern Theme**: Professional "cosmo" theme with blue accents
- **Native Components**: OS-integrated dialogs and controls

---

### 1. 🏠 Home Dashboard

The home page provides:

#### Feature Cards

Four prominent cards highlighting key capabilities:

1. **🚀 Blazingly Fast**
   - Async-first architecture
   - 10-100x faster than traditional crawlers
   - Concurrent downloads with semaphore control

2. **🔐 Advanced Authentication**
   - Stealth mode bypasses bot detection
   - Cookie-based persistent sessions
   - Support for 2FA and complex logins

3. **🎯 Smart Crawling**
   - Intelligent link discovery
   - Asset extraction (CSS, JS, images, fonts)
   - Respects robots.txt and rate limits

4. **📊 Comprehensive Analytics**
   - Detailed metrics and reports
   - Real-time progress tracking
   - Export capabilities

#### Quick Start Guide

Step-by-step workflow overview:
1. (Optional) Set up authentication
2. Navigate to 'Crawl Website'
3. Enter URL and configure
4. Start crawl and monitor
5. View results

#### Action Buttons

- **🔐 Set Up Authentication** - Jump to auth page
- **📥 Start Crawling Now** - Jump to crawl page

**Use Case:** First-time users should start here to understand the workflow.

---

### 2. 🔐 Authentication Manager

Manage authenticated sessions for protected websites using a tabbed interface.

#### Tab 1: 🆕 New Login

Create new authenticated sessions:

**Login Configuration**

1. **Login URL**
   - Enter the site's login page URL
   - Example: `https://accounts.google.com`
   - Example: `https://www.facebook.com/login`
   - Must be a valid HTTP/HTTPS URL

2. **Session Name**
   - Choose a memorable, descriptive name
   - Good: `google_work`, `facebook_personal`, `github_private`
   - Bad: `session1`, `temp`, `test`
   - Used as filename: `cookies/[session_name].json`

**Workflow**

1. Fill in Login URL and Session Name
2. Click **"🌐 Open Browser for Login"**
   - Chrome browser opens with stealth mode enabled
   - Navigator.webdriver is masked
   - Google Cloud Services disabled
   - Bot detection bypassed
3. Manually log in to the site
   - Enter username/password
   - Complete 2FA if required
   - Solve CAPTCHAs if needed
   - Navigate to your target page
4. Click **"💾 Save Session & Cookies"**
   - All cookies are saved to `./cookies/[session_name].json`
   - Browser closes automatically
   - Session ready for use!

**Status Messages**
- "Opening browser..." - Browser launching
- "✅ Browser opened!" - Ready for login
- "✅ Session saved!" - Complete

#### Tab 2: 💾 Saved Sessions

View and manage existing cookie files:

**Session List (Treeview)**

Columns displayed:
- **Session Name** - Your chosen identifier
- **Created Date** - When cookies were saved
- **Domain** - Primary domain of cookies

**Actions**

- **🔄 Refresh List** - Reload saved sessions
- **🗑️ Delete Selected** - Remove unwanted sessions
  - Prompts for confirmation
  - Permanently deletes cookie file
- **📂 Open Cookies Folder** - View in file explorer
  - Windows: Opens in Explorer
  - macOS: Opens in Finder
  - Linux: Opens in file manager

**Use Case:** Organize multiple accounts (work, personal, test environments)

#### Tab 3: ❓ Help

Comprehensive authentication guide including:
- Why authenticate
- How it works
- Supported sites
- Security considerations
- Troubleshooting tips

#### Supported Sites

WebMirror's stealth mode works with:

- ✅ **Google** (Gmail, Drive, Docs, Photos, etc.)
- ✅ **Facebook** (profiles, groups, pages)
- ✅ **LinkedIn** (profiles, connections)
- ✅ **Twitter/X** (timelines, profiles)
- ✅ **GitHub** (private repos, gists)
- ✅ **GitLab** (private projects)
- ✅ **Bitbucket** (private repos)
- ✅ **Any cookie-based authentication system**

---

### 3. 📥 Crawl Website

The main interface for configuring and running crawls.

#### Basic Configuration

**Website URL**
- The starting point for your crawl
- Must be a valid HTTP/HTTPS URL
- Example: `https://example.com`
- Example: `https://docs.python.org/3/`

**Output Directory**
- Where downloaded files will be saved
- Default: `./website_mirror`
- Created automatically if doesn't exist
- Subdirectories created:
  - `pages/` - HTML pages
  - `assets/` - CSS, JS, images, fonts
  - `pdfs/` - PDF snapshots (if enabled)
  - `reports/` - Crawl metadata
- Use **Browse...** button for native file dialog

#### Advanced Settings (Expandable)

**Crawling Options (Left Column)**

1. **Recursive Crawl** (toggle)
   - ✅ Enabled: Follow links to other pages
   - ❌ Disabled: Only download start URL
   - Recommended: Enabled for full site mirrors

2. **Same Domain Only** (toggle)
   - ✅ Enabled: Only crawl URLs on same domain
   - ❌ Disabled: Follow external links too
   - Recommended: Enabled to avoid downloading entire internet

3. **Include Assets** (toggle)
   - ✅ Enabled: Download CSS, JS, images, fonts
   - ❌ Disabled: HTML pages only
   - Recommended: Enabled for complete offline viewing

4. **Generate PDFs** (toggle)
   - ✅ Enabled: Create PDF snapshots of each page
   - ❌ Disabled: Skip PDF generation
   - Note: Slower crawl, larger storage
   - Recommended: Disabled for most use cases

**Performance Options (Right Column)**

| Setting | Range | Description | Recommended |
|---------|-------|-------------|-------------|
| **Workers** | 1-50 | Concurrent download threads | 5-10 |
| **Delay (ms)** | 0-5000 | Pause between requests | 100-1000 |
| **Max Depth** | 0-10 | How deep to follow links | 0 (unlimited) |
| **Max Pages** | 0-10000 | Maximum pages to download | 0 (unlimited) |

**Configuration Tips:**

- **Fast crawl, gentle site**: Workers=10, Delay=100ms
- **Slow crawl, avoid detection**: Workers=3, Delay=2000ms
- **Test run**: Max Pages=10, Max Depth=2
- **Full mirror**: All defaults (unlimited)

#### Authentication (Optional)

**Cookie File Selection**

- Dropdown shows all saved sessions
- Default: "None" (no authentication)
- Select a session to use saved cookies
- Click **🔄 Refresh** to reload list after creating new sessions

**When to Use:**
- ✅ Site requires login
- ✅ Content behind paywall
- ✅ Private repositories
- ✅ Personal accounts
- ❌ Public websites (leave as "None")

#### Control Buttons

**▶️ Start Crawl** (Large green button)
- Begins the crawl operation
- Disabled during active crawl
- Validates configuration first
- Starts background thread

**⏹️ Stop Crawl** (Large red button)
- Stops crawl immediately
- Enabled during active crawl
- Saves partial results
- Cleans up resources

#### Progress Section

**Progress Bar**
- Visual indicator of completion
- Updates in real-time
- Striped animation shows activity

**Status Text**
- Current operation description
- Examples:
  - "Ready to start crawling..."
  - "Initializing crawl..."
  - "Crawling: https://example.com/page1"
  - "✅ Crawl completed successfully!"
  - "❌ Error: [error message]"

**Live Statistics**

Four real-time counters:

1. **Pages: X** - HTML pages downloaded
2. **Assets: X** - CSS, JS, images downloaded
3. **Size: X MB** - Total data downloaded
4. **Time: Xs** - Elapsed time

Updates every 500ms during crawl.

---

### 4. 📊 Results & Analytics

View detailed statistics and download reports.

#### When No Results

If you haven't completed a crawl:
- Shows friendly message
- **📥 Start a Crawl** button navigates to crawl page

#### Summary Cards

Four large metric cards at the top:

1. **📄 Pages Crawled**
   - Total HTML pages downloaded
   - Large blue number display

2. **📦 Assets Downloaded**
   - CSS, JS, images, fonts, etc.
   - Large info-colored number

3. **💾 Total Size**
   - Combined size in MB (with 2 decimals)
   - Large green number

4. **⏱️ Duration**
   - Total crawl time in seconds
   - Large yellow number

#### Detailed Results (Tabbed Interface)

**Tab 1: 📄 Pages**

Sortable table (Treeview) with columns:
- **URL** - Full page URL (400px wide)
- **Status** - HTTP status code (80px)
- **Depth** - Link depth from start URL (80px)
- **Links** - Number of links found (80px)
- **Assets** - Number of assets found (80px)

Scrollable for large result sets.

**Tab 2: 📦 Assets**

Asset distribution by type:
- Grouped count display
- Shows: HTML, CSS, JAVASCRIPT, IMAGE, FONT, etc.
- Monospace font for alignment
- Example output:
  ```
  Asset Distribution:

  CSS: 15
  HTML: 42
  IMAGE: 127
  JAVASCRIPT: 23
  ```

**Tab 3: 💾 Export**

Export options:

1. **📥 Export as JSON**
   - Opens native "Save As" dialog
   - Saves complete metadata as JSON
   - Includes all pages, assets, timestamps
   - Default filename: `[domain]_crawl_results.json`

2. **📂 Open Output Directory**
   - Opens file explorer at output location
   - Quick access to downloaded files
   - OS-specific:
     - Windows: `explorer`
     - macOS: `open`
     - Linux: `xdg-open`

---

## 💡 Usage Examples

### Example 1: Simple Public Website

**Scenario:** Archive a blog for offline reading

```
1. Launch GUI: make gui
2. Navigate to "📥 Crawl Website"
3. URL: https://myblog.com
4. Settings:
   ✅ Recursive
   ✅ Same Domain Only
   ✅ Include Assets
   Workers: 10
   Delay: 100ms
5. Click "▶️ Start Crawl"
6. Monitor progress in real-time
7. Click "📊 Results & Analytics" when done
8. Review statistics and export if desired
```

**Expected Time:** 30 seconds - 5 minutes (depends on site size)

### Example 2: Authenticated Site (Google Drive)

**Scenario:** Download documents from Google Drive

```
Phase 1: Authentication (One Time)
1. Launch GUI: make gui
2. Navigate to "🔐 Authentication"
3. Tab: "🆕 New Login"
4. Login URL: https://accounts.google.com
5. Session Name: google_drive_personal
6. Click "🌐 Open Browser for Login"
7. Log in to Google (username, password, 2FA)
8. Navigate to Google Drive
9. Click "💾 Save Session & Cookies"

Phase 2: Crawl (Every Time)
1. Navigate to "📥 Crawl Website"
2. URL: https://drive.google.com/drive/folders/[YOUR_FOLDER_ID]
3. Authentication: Select "google_drive_personal"
4. Settings:
   ✅ Recursive
   Max Depth: 3
   Workers: 5 (gentle on Google)
   Delay: 500ms
5. Click "▶️ Start Crawl"
6. View results in "📊 Results & Analytics"
```

**Expected Time:** 2-10 minutes (depends on content)

### Example 3: Large Documentation Site

**Scenario:** Clone Python docs without getting blocked

```
1. Launch GUI: make gui
2. Navigate to "📥 Crawl Website"
3. URL: https://docs.python.org/3/
4. Advanced Settings:
   ✅ Recursive
   ✅ Same Domain Only
   ✅ Include Assets
   ❌ Generate PDFs (too slow)
   Max Pages: 200 (limit scope)
   Workers: 5 (be gentle)
   Delay: 1000ms (1 second between requests)
5. Click "▶️ Start Crawl"
6. Go get coffee ☕
7. Monitor in "📊 Results & Analytics"
```

**Expected Time:** 10-30 minutes

### Example 4: Test Run Before Full Crawl

**Scenario:** Preview what will be downloaded

```
1. Launch GUI: make gui
2. Navigate to "📥 Crawl Website"
3. URL: https://unknownsite.com
4. Settings (Conservative):
   ✅ Recursive
   Max Depth: 2 (only go 2 links deep)
   Max Pages: 10 (stop after 10 pages)
   Workers: 3
   Delay: 500ms
5. Click "▶️ Start Crawl"
6. Review results
7. If good, run again with unlimited settings
```

**Expected Time:** 30 seconds - 2 minutes

---

## ⚙️ Configuration

### Environment Variables

Create `.env` file in project root:

```bash
# Selenium Configuration
WEBMIRROR_SELENIUM_HEADLESS=false  # Show browser (for debugging)
WEBMIRROR_SELENIUM_TIMEOUT=30

# Crawler Configuration
WEBMIRROR_WORKERS=5
WEBMIRROR_DELAY_MS=100
WEBMIRROR_MAX_PAGES=0  # 0 = unlimited
```

### Cookie Storage

Location: `./cookies/` directory

**File Format:** JSON
```json
[
  {
    "name": "session_id",
    "value": "abc123...",
    "domain": ".google.com",
    "path": "/",
    "expires": 1735689600,
    "secure": true,
    "httpOnly": true
  }
]
```

**Security:**
- ⚠️ Never commit to git (already in `.gitignore`)
- ⚠️ Treat like passwords
- ⚠️ Don't share or email
- ⚠️ Store securely

---

## 🐛 Troubleshooting

### GUI Won't Start

**Problem:** ImportError or module not found

**Solutions:**
```bash
# Reinstall GUI dependencies
make install-gui

# Or manually
pip install ttkbootstrap>=1.10.1

# Verify installation
python -c "import ttkbootstrap; print(ttkbootstrap.__version__)"
```

### GUI Looks Broken/Ugly

**Problem:** Missing ttkbootstrap, falling back to basic Tkinter

**Solution:**
```bash
# Install ttkbootstrap for modern theme
pip install ttkbootstrap>=1.10.1
```

**Verify:** Application title should say "WebMirror" and have blue theme

### Browser Won't Open for Auth

**Problem:** "Chrome not found" or "WebDriver error"

**Solutions:**

1. Install Chrome/Chromium:
   ```bash
   # Ubuntu/Debian
   sudo apt install chromium-browser

   # Fedora
   sudo dnf install chromium

   # macOS
   brew install --cask google-chrome

   # Windows
   # Download from: https://www.google.com/chrome/
   ```

2. Update WebDriver:
   ```bash
   pip install --upgrade selenium webdriver-manager
   ```

3. Verify Chrome installation:
   ```bash
   google-chrome --version
   # or
   chromium --version
   ```

### Cookies Not Working

**Problem:** Still getting "Login required" or access denied

**Possible Causes & Solutions:**

1. **Session Expired**
   - Cookie lifetime depends on site (1-30 days typical)
   - Solution: Delete old cookie file, re-authenticate

2. **Domain Mismatch**
   - Cookies saved for `accounts.google.com`
   - Trying to access `drive.google.com`
   - Solution: Make sure to navigate to target domain during login

3. **IP Address Changed**
   - Some sites invalidate cookies on IP change
   - Solution: Re-authenticate from new IP

4. **2FA Required Again**
   - Site requires periodic 2FA verification
   - Solution: Complete 2FA during manual login

5. **Cookie File Corrupted**
   - JSON parse error
   - Solution: Delete and recreate session

### Slow Crawling

**Problem:** Taking too long

**Optimization Steps:**

1. **Increase Workers**
   ```
   Workers: 10-20 (from 5)
   ```

2. **Reduce Delay**
   ```
   Delay: 50-100ms (from 500ms)
   ```

3. **Limit Scope**
   ```
   Max Pages: 100
   Max Depth: 3
   ```

4. **Disable PDF Generation**
   ```
   ❌ Generate PDFs (uncheck)
   ```

5. **Disable Asset Download** (HTML only)
   ```
   ❌ Include Assets (uncheck)
   ```

### High Memory Usage

**Problem:** GUI freezes or system slows down

**Solutions:**

1. **Reduce Workers**
   ```
   Workers: 3 (from 10)
   ```

2. **Increase Delay**
   ```
   Delay: 1000ms (1 second)
   ```

3. **Limit Pages**
   ```
   Max Pages: 50-100
   ```

4. **Close Other Applications**

5. **Increase System RAM** (if possible)

### Crawl Stops/Fails

**Problem:** Error message or unexpected stop

**Common Errors:**

1. **Network Error**
   - Check internet connection
   - Try again with higher delay

2. **Permission Denied**
   - Output directory not writable
   - Choose different output location

3. **Rate Limited**
   - Site detected high request rate
   - Increase delay_ms
   - Reduce workers

4. **Invalid URL**
   - Check URL format
   - Must start with `http://` or `https://`

---

## 🔒 Security & Privacy

### Cookie Security

**Storage:**
- Cookies stored locally in `./cookies/` directory
- Plain JSON format (not encrypted)
- Only readable by your user account

**Transmission:**
- Never sent to remote servers
- WebMirror has no telemetry or analytics
- All processing is local

**Expiry:**
- Cookies expire per site's policy
- Typically 1-30 days
- Must re-authenticate when expired

### Best Practices

1. **Don't Share Cookie Files**
   - Contain authentication tokens
   - Same as sharing your password
   - Can grant full account access

2. **Use Dedicated Accounts**
   - Create separate accounts for scraping
   - Don't use primary personal accounts
   - Reduces risk if compromised

3. **Rotate Sessions Regularly**
   - Re-authenticate periodically
   - Delete old cookie files
   - Keep organized

4. **Check Terms of Service**
   - Ensure scraping is allowed
   - Some sites prohibit automated access
   - Respect site policies

5. **Respect Rate Limits**
   - Use appropriate delays
   - Don't overwhelm servers
   - Be a good internet citizen

6. **Secure Your Computer**
   - Cookie files as secure as your system
   - Use disk encryption
   - Strong user password

---

## 📞 Support

### Getting Help

- 📖 **Documentation**: `docs/` directory
- 📖 **Quick Start**: `GUI_QUICKSTART.md`
- 📖 **Authentication**: `docs/AUTHENTICATION_GUIDE.md`
- 💬 **GitHub Issues**: https://github.com/ruslanmv/webmirror/issues
- 📧 **Email**: contact@ruslanmv.com
- 🌐 **Website**: ruslanmv.com

### Reporting Bugs

When reporting issues, include:

1. **Environment**
   - OS: Windows/macOS/Linux + version
   - Python version: `python --version`
   - WebMirror version: Check `pyproject.toml`

2. **Steps to Reproduce**
   - Exact sequence of actions
   - Configuration used
   - URL being crawled (if not private)

3. **Error Messages**
   - Complete error text
   - Stack traces if available
   - Screenshots of GUI (if relevant)

4. **Expected vs Actual**
   - What you expected to happen
   - What actually happened

### Feature Requests

Open a GitHub issue with:
- Clear description of desired feature
- Use case / motivation
- Proposed implementation (if applicable)

---

## 🎓 Tips & Tricks

### Performance Optimization

1. **Start Small**
   - Test with `Max Pages: 10` first
   - Verify configuration works
   - Then expand to full crawl

2. **Tune Workers**
   - More isn't always better
   - CPU-bound: workers ≈ CPU cores
   - I/O-bound: workers = 5-10 optimal
   - Experiment to find sweet spot

3. **Use Delays Strategically**
   - Public sites: 100-500ms sufficient
   - Protected sites: 1000-2000ms safer
   - Prevents rate limiting
   - Reduces server load

4. **Same Domain Only**
   - Prevents downloading external assets
   - CDNs, analytics, ads
   - Significantly faster
   - More focused content

### Authentication Tips

1. **Save Multiple Sessions**
   - One per site/account
   - Example: `google_work`, `google_personal`
   - Easy to switch between

2. **Use Descriptive Names**
   - ✅ Good: `github_company_repos`, `facebook_marketing`
   - ❌ Bad: `session1`, `temp`, `test123`

3. **Test Cookies Immediately**
   - After saving, do a small test crawl
   - Verify authentication works
   - Catch issues early

4. **Refresh Periodically**
   - Sessions expire (1-30 days)
   - Re-authenticate weekly for active use
   - Delete stale sessions

### Content Selection

**HTML Only** (fastest, smallest):
```
❌ Include Assets
❌ Generate PDFs
Max Pages: Unlimited
```

**Full Mirror** (complete, large):
```
✅ Include Assets
❌ Generate PDFs (unless needed)
✅ Recursive
Max Pages: Unlimited
```

**Quick Preview** (test run):
```
✅ Include Assets
Max Pages: 10
Max Depth: 2
```

**Documentation Archive** (text-focused):
```
✅ Include Assets (for CSS/readability)
❌ Generate PDFs
Same Domain Only
```

---

## 🆚 Desktop GUI vs CLI

### When to Use Desktop GUI

✅ **Visual workflow preferred**
✅ **First-time users**
✅ **Point-and-click configuration**
✅ **Real-time progress monitoring**
✅ **Managing multiple cookie sessions**
✅ **Interactive authentication**
✅ **Windows users (GUI is easier)**

### When to Use CLI

✅ **Automation/scripting**
✅ **CI/CD pipelines**
✅ **Remote servers (SSH)**
✅ **Batch operations**
✅ **Configuration files (reproducible)**
✅ **Power users**
✅ **Headless environments**

### CLI Quick Reference

```bash
# Basic crawl
webmirror clone https://example.com

# With options
webmirror clone https://example.com \
  --output ./mirror \
  --workers 10 \
  --delay-ms 100 \
  --max-depth 3 \
  --recursive

# With authentication
webmirror clone https://protected.com \
  --cookie-file ./cookies/my_session.json

# Help
webmirror --help
webmirror clone --help
```

---

## 🎯 Advanced Usage

### Batch Crawling Multiple Sites

Use the GUI for each site individually, or automate with CLI:

```bash
#!/bin/bash
# batch_crawl.sh

sites=(
  "https://site1.com"
  "https://site2.com"
  "https://site3.com"
)

for site in "${sites[@]}"; do
  webmirror clone "$site" --max-pages 50
done
```

### Scheduled Crawls

**Linux/Mac (cron):**
```bash
# Edit crontab
crontab -e

# Run daily at 2 AM
0 2 * * * cd /path/to/webmirror && webmirror clone https://example.com
```

**Windows (Task Scheduler):**
- Open Task Scheduler
- Create Basic Task
- Trigger: Daily
- Action: Start Program
  - Program: `python`
  - Arguments: `-m webmirror.cli clone https://example.com`
  - Start in: `C:\path\to\webmirror`

### Custom Configuration Files

Create `crawl_config.json`:
```json
{
  "start_url": "https://example.com",
  "output_dir": "./mirror",
  "recursive": true,
  "workers": 10,
  "delay_ms": 100
}
```

Load via CLI:
```bash
webmirror clone --config crawl_config.json
```

---

## 🏆 Advantages of Enterprise Desktop GUI

### vs Web-Based GUIs (Streamlit, Flask, etc.)

✅ **Instant Startup** - No server to launch, opens in <1 second
✅ **Native Performance** - No browser overhead, direct system calls
✅ **Better Responsiveness** - No HTTP roundtrips
✅ **No Port Conflicts** - Doesn't need localhost ports
✅ **Offline Friendly** - Works without network (except crawling)
✅ **Native File Dialogs** - OS-integrated file/folder selection
✅ **System Integration** - Taskbar, notifications, multi-monitor
✅ **Resource Efficient** - Lower memory and CPU usage
✅ **Professional Appearance** - Modern theme matches OS
✅ **Easier Distribution** - Single executable possible

### vs Command-Line Interface

✅ **Visual Configuration** - See all options at once
✅ **No Syntax Errors** - Point-and-click vs typing commands
✅ **Real-Time Feedback** - Progress bars, live stats
✅ **Easier Authentication** - Integrated browser workflow
✅ **Session Management** - Visual cookie file selection
✅ **Results Viewing** - Tables, cards, charts (vs plain text)
✅ **Lower Learning Curve** - Intuitive for non-technical users
✅ **Discoverability** - All features visible in UI

---

**Author**: Ruslan Magana
**Website**: [ruslanmv.com](https://ruslanmv.com)
**License**: Apache 2.0

---

*Happy Crawling with WebMirror Enterprise Desktop GUI! 🚀*
