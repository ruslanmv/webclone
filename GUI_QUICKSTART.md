# 🚀 WebMirror GUI - 2-Minute Quick Start

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

After launching, your browser opens to: `http://localhost:8501`

You'll see a beautiful dashboard with navigation sidebar.

### Step 2: (Optional) Authenticate

**Skip this if crawling public sites!**

For sites requiring login (Google, Facebook, etc.):

1. Click **"Authentication"** in sidebar
2. Enter login URL (e.g., `https://accounts.google.com`)
3. Give it a name (e.g., `my_google`)
4. Click **"Open Browser for Login"**
5. Log in normally in the opened browser
6. Click **"Save Session & Cookies"**

✅ Done! Cookies saved for future use.

### Step 3: Start Crawling

1. Click **"Crawl Website"** in sidebar
2. Enter target URL
3. Adjust settings (or use defaults)
4. Click **"▶️ Start Crawl"**
5. Watch real-time progress
6. View results when done!

---

## Example: Clone a Blog (No Login)

```
1. Launch GUI: make gui
2. Go to "Crawl Website"
3. URL: https://example-blog.com
4. Click "Start Crawl"
5. Done!
```

**Time:** ~30 seconds (for small sites)

---

## Example: Download from Google Drive

```
1. Launch GUI: make gui
2. Go to "Authentication"
3. URL: https://accounts.google.com
4. Name: google_drive
5. Click "Open Browser"
6. Log in to Google
7. Click "Save Session"
8. Go to "Crawl Website"
9. URL: https://drive.google.com/drive/...
10. Click "Start Crawl"
11. Done!
```

**Time:** ~2 minutes (including login)

---

## Troubleshooting

### GUI Won't Start

```bash
# Reinstall dependencies
make install-gui

# Or manually
pip install streamlit streamlit-option-menu
```

### Port Already in Use

```bash
# Use different port
streamlit run src/webmirror/gui/streamlit_app.py --server.port 8502
```

### Browser Won't Open for Auth

- Install Chrome or Chromium
- Check: `google-chrome --version`

---

## Need More Help?

- **Full GUI Guide**: `docs/GUI_GUIDE.md`
- **Authentication Help**: `docs/AUTHENTICATION_GUIDE.md`
- **CLI Alternative**: `webmirror --help`
- **Issues**: https://github.com/ruslanmv/webmirror/issues

---

**That's it! You're ready to use WebMirror!** 🎉

**Author**: Ruslan Magana | **Website**: ruslanmv.com
