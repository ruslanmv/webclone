# 🚀 WebMirror Enterprise Desktop GUI - 2-Minute Quick Start

## Installation (One Time)

```bash
# Install WebMirror with GUI
make install-gui
```

That's it! Installation complete.

---

## Launch GUI

### Method 1: Using Make (Recommended)
```bash
make gui
```

### Method 2: Double-Click Launcher

**On Linux/Mac:**
- Double-click `webmirror-gui.py`

**On Windows:**
- Double-click `webmirror-gui.bat`

### Method 3: Python Command
```bash
python webmirror-gui.py
```

---

## First Use - 3 Simple Steps

### Step 1: Open the GUI

After launching, the WebMirror Enterprise Desktop GUI opens instantly.

You'll see a beautiful desktop application with a sidebar navigation and clean interface.

### Step 2: (Optional) Authenticate

**Skip this if crawling public sites!**

For sites requiring login (Google, Facebook, etc.):

1. Click **"🔐 Authentication"** in sidebar
2. Go to **"🆕 New Login"** tab
3. Enter login URL (e.g., `https://accounts.google.com`)
4. Give it a name (e.g., `my_google`)
5. Click **"🌐 Open Browser for Login"**
6. Log in normally in the opened browser
7. Click **"💾 Save Session & Cookies"**

✅ Done! Cookies saved for future use.

### Step 3: Start Crawling

1. Click **"📥 Crawl Website"** in sidebar
2. Enter target URL
3. Adjust settings (or use defaults)
4. Click **"▶️ Start Crawl"**
5. Watch real-time progress
6. View results when done!

---

## Example: Clone a Blog (No Login)

```
1. Launch GUI: make gui
2. Click "📥 Crawl Website"
3. URL: https://example-blog.com
4. Click "▶️ Start Crawl"
5. Done!
```

**Time:** ~30 seconds (for small sites)

---

## Example: Download from Google Drive

```
1. Launch GUI: make gui
2. Click "🔐 Authentication"
3. Tab: "🆕 New Login"
4. URL: https://accounts.google.com
5. Name: google_drive
6. Click "🌐 Open Browser"
7. Log in to Google
8. Click "💾 Save Session"
9. Click "📥 Crawl Website"
10. URL: https://drive.google.com/drive/...
11. Select cookie: "google_drive"
12. Click "▶️ Start Crawl"
13. Done!
```

**Time:** ~2 minutes (including login)

---

## Advantages Over Web-Based GUIs

✅ **Native Desktop Performance** - Faster, no browser overhead
✅ **Instant Startup** - No server to launch, opens immediately
✅ **Better OS Integration** - Native file dialogs, system notifications
✅ **No Port Conflicts** - Runs directly, no localhost ports
✅ **Offline Friendly** - No web dependencies after installation
✅ **Professional Look** - Modern theme matches your OS

---

## Troubleshooting

### GUI Won't Start

```bash
# Reinstall dependencies
make install-gui

# Or manually
pip install ttkbootstrap
```

### Missing ttkbootstrap

```bash
# Install directly
pip install ttkbootstrap>=1.10.1
```

### Browser Won't Open for Auth

- Install Chrome or Chromium
- Check: `google-chrome --version`

---

## Navigation Overview

The GUI has 4 main pages accessible from the left sidebar:

### 🏠 Home
- Feature overview
- Quick start guide
- System status

### 🔐 Authentication
- **New Login** - Authenticate to protected sites
- **Saved Sessions** - Manage saved cookies
- **Help** - Authentication guide

### 📥 Crawl Website
- Configure target URL
- Set crawl options
- Monitor real-time progress
- View live statistics

### 📊 Results & Analytics
- View crawl summary
- Browse downloaded pages
- Analyze assets
- Export results

---

## Need More Help?

- **Full GUI Guide**: `docs/GUI_GUIDE.md`
- **Authentication Help**: `docs/AUTHENTICATION_GUIDE.md`
- **CLI Alternative**: `webmirror --help`
- **Issues**: https://github.com/ruslanmv/webmirror/issues

---

**That's it! You're ready to use WebMirror Enterprise Desktop GUI!** 🎉

**Author**: Ruslan Magana | **Website**: ruslanmv.com
