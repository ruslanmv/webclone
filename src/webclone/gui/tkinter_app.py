#!/usr/bin/env python3
"""
WebClone Enterprise GUI - Professional Tkinter Application

A world-class desktop interface for website cloning with:
- Modern, enterprise-grade design
- Persistent browser sessions
- Automatic URL synchronization
- Session reload capability
- View downloaded sites
- Production-grade logging

Author: Ruslan Magana
Website: ruslanmv.com
License: Apache 2.0
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any, Optional

import tkinter as tk

# ======================================================================
# LOGGING SETUP
# ======================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('webclone_gui.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

logger.info("=" * 80)
logger.info("WebClone GUI Application Starting")
logger.info("=" * 80)

# ======================================================================
# Unified Tk / ttk / ttkbootstrap backend selection
# ======================================================================

USING_TTKBOOTSTRAP = False
tb = None

try:
    import ttkbootstrap as _tb
    from ttkbootstrap import ttk as _ttk
    from ttkbootstrap.constants import *  # noqa: F401,F403

    if not hasattr(_tb, "Window") or not hasattr(_ttk, "LabelFrame"):
        raise RuntimeError("ttkbootstrap incompatible")

    tb = _tb
    ttk = _ttk  # type: ignore[assignment]
    USING_TTKBOOTSTRAP = True
    logger.info("Using ttkbootstrap for modern UI")

except ImportError:
    from tkinter import ttk
    from tkinter.constants import *  # noqa: F401,F403
    USING_TTKBOOTSTRAP = False
    logger.warning("ttkbootstrap not available; using standard tkinter")

except RuntimeError:
    from tkinter import ttk
    from tkinter.constants import *  # noqa: F401,F403
    USING_TTKBOOTSTRAP = False
    logger.warning("ttkbootstrap found but incompatible; using standard tkinter")

from webclone.core.crawler import AsyncCrawler
from webclone.models.config import CrawlConfig, SeleniumConfig
from webclone.models.metadata import CrawlResult
from webclone.services.selenium_service import SeleniumService


class WebCloneGUI:
    """Enterprise-grade Tkinter GUI for WebClone."""

    def __init__(self) -> None:
        """Initialize the GUI application."""
        logger.info("Initializing WebClone GUI")
        
        # Create root window
        if USING_TTKBOOTSTRAP and tb is not None:
            self.root = tb.Window(themename="cosmo")
            logger.info("Created ttkbootstrap Window with cosmo theme")
        else:
            self.root = tk.Tk()
            logger.info("Created standard Tk Window")

        self.root.title("WebClone - Professional Website Cloning Engine")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)

        # Application state
        self.current_page = "home"
        self.crawler_thread: Optional[threading.Thread] = None
        self.is_crawling = False
        self.crawl_metadata: Optional[CrawlResult] = None
        self.selenium_service: Optional[SeleniumService] = None
        self.saved_cookies: list[Path] = []
        
        # Browser monitoring
        self.browser_active = False
        self.url_monitor_thread: Optional[threading.Thread] = None
        self.stop_url_monitor = False
        self.current_browser_url = ""
        self.saved_session_url = ""  # Store URL when session is saved

        logger.info("Application state initialized")

        # Initialize UI
        self._setup_styles()
        self._create_layout()
        self._load_saved_cookies()
        self._show_page("home")
        
        logger.info("GUI initialization complete")

    # ======================================================================
    # STYLES & LAYOUT
    # ======================================================================

    def _setup_styles(self) -> None:
        """Configure custom styles for professional appearance."""
        logger.info("Setting up custom styles")
        try:
            style = ttk.Style()

            # Configure custom button styles
            style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))
            style.configure("Large.TButton", font=("Segoe UI", 12, "bold"), padding=10)

            # Configure label styles
            style.configure("Title.TLabel", font=("Segoe UI", 24, "bold"))
            style.configure("Subtitle.TLabel", font=("Segoe UI", 14))
            style.configure("Heading.TLabel", font=("Segoe UI", 16, "bold"))
            style.configure("Body.TLabel", font=("Segoe UI", 10))
            
            logger.info("Custom styles configured successfully")
        except Exception as e:
            logger.error(f"Error configuring styles: {e}", exc_info=True)

    def _create_layout(self) -> None:
        """Create the main application layout."""
        logger.info("Creating main application layout")
        
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=BOTH, expand=YES, padx=0, pady=0)

        # Sidebar (left)
        self._create_sidebar(main_container)

        # Content area (right)
        self.content_frame = ttk.Frame(main_container)
        self.content_frame.pack(side=LEFT, fill=BOTH, expand=YES, padx=20, pady=20)
        
        logger.info("Main layout created successfully")

    def _create_sidebar(self, parent: ttk.Frame) -> None:
        """Create navigation sidebar."""
        logger.info("Creating navigation sidebar")
        
        sidebar_kwargs: dict[str, Any] = {"width": 250}
        if USING_TTKBOOTSTRAP:
            sidebar_kwargs["bootstyle"] = "secondary"
        sidebar = ttk.Frame(parent, **sidebar_kwargs)
        sidebar.pack(side=LEFT, fill=Y, padx=0, pady=0)
        sidebar.pack_propagate(False)

        # Logo/Title
        logo_kwargs: dict[str, Any] = {}
        if USING_TTKBOOTSTRAP:
            logo_kwargs["bootstyle"] = "secondary"
        logo_frame = ttk.Frame(sidebar, **logo_kwargs)
        logo_frame.pack(fill=X, padx=20, pady=30)

        title_kwargs: dict[str, Any] = {
            "text": "🌐 WebClone",
            "font": ("Segoe UI", 20, "bold"),
        }
        if USING_TTKBOOTSTRAP:
            title_kwargs["bootstyle"] = "inverse-secondary"
        title = ttk.Label(logo_frame, **title_kwargs)
        title.pack()

        subtitle_kwargs: dict[str, Any] = {
            "text": "Enterprise Edition",
            "font": ("Segoe UI", 9),
        }
        if USING_TTKBOOTSTRAP:
            subtitle_kwargs["bootstyle"] = "inverse-secondary"
        subtitle = ttk.Label(logo_frame, **subtitle_kwargs)
        subtitle.pack()

        # Navigation buttons
        nav_kwargs: dict[str, Any] = {}
        if USING_TTKBOOTSTRAP:
            nav_kwargs["bootstyle"] = "secondary"
        nav_frame = ttk.Frame(sidebar, **nav_kwargs)
        nav_frame.pack(fill=BOTH, expand=YES, padx=10, pady=10)

        nav_buttons = [
            ("🏠 Home", "home", "primary"),
            ("🔐 Authentication", "auth", "info"),
            ("📥 Crawl Website", "crawl", "success"),
            ("📊 Results & Analytics", "results", "warning"),
        ]

        for text, page_id, bootstyle in nav_buttons:
            btn_kwargs: dict[str, Any] = {
                "text": text,
                "command": (lambda p=page_id: self._show_page(p)),
                "width": 25,
            }
            if USING_TTKBOOTSTRAP:
                btn_kwargs["bootstyle"] = f"{bootstyle}-outline"
            btn = ttk.Button(nav_frame, **btn_kwargs)
            btn.pack(pady=5, fill=X)

        # Footer
        footer_kwargs: dict[str, Any] = {}
        if USING_TTKBOOTSTRAP:
            footer_kwargs["bootstyle"] = "secondary"
        footer = ttk.Frame(sidebar, **footer_kwargs)
        footer.pack(side=BOTTOM, fill=X, padx=20, pady=20)

        footer_label_kwargs: dict[str, Any] = {
            "text": "© 2025 Ruslan Magana\nruslanmv.com",
            "font": ("Segoe UI", 8),
            "justify": CENTER,
        }
        if USING_TTKBOOTSTRAP:
            footer_label_kwargs["bootstyle"] = "inverse-secondary"
        footer_text = ttk.Label(footer, **footer_label_kwargs)
        footer_text.pack()
        
        logger.info("Sidebar created successfully")

    def _show_page(self, page_id: str) -> None:
        """Switch to a different page."""
        logger.info(f"Switching to page: {page_id}")
        
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        self.current_page = page_id

        # Show requested page
        if page_id == "home":
            self._create_home_page()
        elif page_id == "auth":
            self._create_auth_page()
        elif page_id == "crawl":
            self._create_crawl_page()
        elif page_id == "results":
            self._create_results_page()

    # ======================================================================
    # HOME PAGE
    # ======================================================================

    def _create_home_page(self) -> None:
        """Create the home/dashboard page."""
        logger.info("Creating home page")
        
        # Page title
        title = ttk.Label(
            self.content_frame,
            text="Welcome to WebClone Enterprise",
            style="Title.TLabel",
        )
        title.pack(pady=(0, 10))

        subtitle_kwargs: dict[str, Any] = {
            "text": "Professional Website Cloning & Archival Engine",
            "style": "Subtitle.TLabel",
        }
        if USING_TTKBOOTSTRAP:
            subtitle_kwargs["bootstyle"] = "secondary"
        subtitle = ttk.Label(self.content_frame, **subtitle_kwargs)
        subtitle.pack(pady=(0, 30))

        # Feature cards
        features_frame = ttk.Frame(self.content_frame)
        features_frame.pack(fill=BOTH, expand=YES)

        # Row 1
        row1 = ttk.Frame(features_frame)
        row1.pack(fill=X, pady=10)

        self._create_feature_card(
            row1,
            "🚀 Blazingly Fast",
            "Async-first architecture with concurrent downloads.\n"
            "10-100x faster than traditional crawlers.",
            "primary",
        ).pack(side=LEFT, fill=BOTH, expand=YES, padx=5)

        self._create_feature_card(
            row1,
            "🔐 Persistent Sessions",
            "Browser stays alive after saving.\n"
            "Continue browsing seamlessly.",
            "info",
        ).pack(side=LEFT, fill=BOTH, expand=YES, padx=5)

        # Row 2
        row2 = ttk.Frame(features_frame)
        row2.pack(fill=X, pady=10)

        self._create_feature_card(
            row2,
            "🎯 Smart Crawling",
            "Intelligent link discovery and asset extraction.\n"
            "Crawls from your current browsing position.",
            "success",
        ).pack(side=LEFT, fill=BOTH, expand=YES, padx=5)

        self._create_feature_card(
            row2,
            "📊 Comprehensive Analytics",
            "Detailed metrics and reports.\n"
            "View downloaded sites locally.",
            "warning",
        ).pack(side=LEFT, fill=BOTH, expand=YES, padx=5)

        # Quick start guide
        guide_frame = ttk.LabelFrame(
            self.content_frame,
            text="⚡ Quick Start Guide",
            padding=20,
        )
        guide_frame.pack(fill=X, pady=30)

        steps = [
            "1️⃣ Set up authentication and browse to your target page",
            "2️⃣ Save session - browser stays alive!",
            "3️⃣ Navigate to 'Crawl Website' - URL is auto-synced",
            "4️⃣ Click 'Start Crawl' from current page",
            "5️⃣ View results and open downloaded site locally",
        ]

        for step in steps:
            lbl = ttk.Label(guide_frame, text=step, font=("Segoe UI", 11))
            lbl.pack(anchor=W, pady=5)

        # Action buttons
        action_frame = ttk.Frame(self.content_frame)
        action_frame.pack(pady=20)

        auth_btn_kwargs: dict[str, Any] = {
            "text": "🔐 Set Up Authentication",
            "command": lambda: self._show_page("auth"),
            "width": 25,
        }
        if USING_TTKBOOTSTRAP:
            auth_btn_kwargs["bootstyle"] = "info"
        ttk.Button(action_frame, **auth_btn_kwargs).pack(side=LEFT, padx=10)

        crawl_btn_kwargs: dict[str, Any] = {
            "text": "📥 Start Crawling Now",
            "command": lambda: self._show_page("crawl"),
            "width": 25,
        }
        if USING_TTKBOOTSTRAP:
            crawl_btn_kwargs["bootstyle"] = "success"
        ttk.Button(action_frame, **crawl_btn_kwargs).pack(side=LEFT, padx=10)

    def _create_feature_card(
        self,
        parent: ttk.Frame,
        title: str,
        description: str,
        bootstyle: str,
    ) -> Any:
        """Create a feature card widget."""
        card_kwargs: dict[str, Any] = {
            "text": title,
            "padding": 15,
        }
        if USING_TTKBOOTSTRAP:
            card_kwargs["bootstyle"] = bootstyle

        card = ttk.LabelFrame(parent, **card_kwargs)

        desc = ttk.Label(
            card,
            text=description,
            wraplength=250,
            justify=LEFT,
        )
        desc.pack()

        return card

    # ======================================================================
    # AUTHENTICATION PAGE
    # ======================================================================

    def _create_auth_page(self) -> None:
        """Create the authentication management page."""
        logger.info("Creating authentication page")
        
        # Page title
        title = ttk.Label(
            self.content_frame,
            text="🔐 Authentication Manager",
            style="Title.TLabel",
        )
        title.pack(pady=(0, 10))

        subtitle_kwargs: dict[str, Any] = {
            "text": "Manage authenticated sessions for protected websites",
            "style": "Subtitle.TLabel",
        }
        if USING_TTKBOOTSTRAP:
            subtitle_kwargs["bootstyle"] = "secondary"
        subtitle = ttk.Label(self.content_frame, **subtitle_kwargs)
        subtitle.pack(pady=(0, 20))

        # Notebook for tabs
        notebook = ttk.Notebook(self.content_frame)
        notebook.pack(fill=BOTH, expand=YES)

        # Tab 1: New Login
        new_login_tab = ttk.Frame(notebook, padding=20)
        notebook.add(new_login_tab, text="🆕 New Login")
        self._create_new_login_tab(new_login_tab)

        # Tab 2: Saved Sessions
        saved_sessions_tab = ttk.Frame(notebook, padding=20)
        notebook.add(saved_sessions_tab, text="💾 Saved Sessions")
        self._create_saved_sessions_tab(saved_sessions_tab)

        # Tab 3: Help
        help_tab = ttk.Frame(notebook, padding=20)
        notebook.add(help_tab, text="❓ Help")
        self._create_auth_help_tab(help_tab)

    def _create_new_login_tab(self, parent: ttk.Frame) -> None:
        """Create new login form."""
        logger.info("Creating new login tab")
        
        # Instructions
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill=X, pady=(0, 20))

        info = ttk.Label(
            info_frame,
            text=(
                "Authenticate to protected websites. Browser stays alive after saving! "
                "Browse to your target page before starting crawl."
            ),
            wraplength=800,
            font=("Segoe UI", 10),
        )
        info.pack()

        # Form
        form_frame = ttk.LabelFrame(parent, text="Login Configuration", padding=20)
        form_frame.pack(fill=X, pady=10)

        # Login URL
        url_frame = ttk.Frame(form_frame)
        url_frame.pack(fill=X, pady=10)

        ttk.Label(url_frame, text="Login URL:", width=20).pack(side=LEFT)
        self.auth_url_var = tk.StringVar(value="https://accounts.google.com")
        url_entry = ttk.Entry(url_frame, textvariable=self.auth_url_var, width=60)
        url_entry.pack(side=LEFT, fill=X, expand=YES, padx=10)

        # Session Name
        name_frame = ttk.Frame(form_frame)
        name_frame.pack(fill=X, pady=10)

        ttk.Label(name_frame, text="Session Name:", width=20).pack(side=LEFT)
        self.session_name_var = tk.StringVar(value="my_session")
        name_entry = ttk.Entry(name_frame, textvariable=self.session_name_var, width=60)
        name_entry.pack(side=LEFT, fill=X, expand=YES, padx=10)

        tip_kwargs: dict[str, Any] = {
            "text": (
                "💡 Tip: Browser stays alive after saving - continue browsing!"
            ),
            "font": ("Segoe UI", 9),
        }
        if USING_TTKBOOTSTRAP:
            tip_kwargs["bootstyle"] = "info"
        ttk.Label(form_frame, **tip_kwargs).pack(pady=5)

        # Browser Status Frame
        status_frame = ttk.LabelFrame(parent, text="🌐 Browser Status", padding=15)
        status_frame.pack(fill=X, pady=10)

        # Status indicator and text
        indicator_frame = ttk.Frame(status_frame)
        indicator_frame.pack(fill=X, pady=5)

        # Create canvas for status indicator (circle)
        self.status_canvas = tk.Canvas(indicator_frame, width=20, height=20, bg='white', highlightthickness=0)
        self.status_canvas.pack(side=LEFT, padx=5)
        self.status_indicator = self.status_canvas.create_oval(2, 2, 18, 18, fill='gray', outline='')

        self.browser_status_var = tk.StringVar(value="Browser not active")
        status_label = ttk.Label(
            indicator_frame,
            textvariable=self.browser_status_var,
            font=("Segoe UI", 10, "bold")
        )
        status_label.pack(side=LEFT, padx=5)

        # Current URL display
        url_display_frame = ttk.Frame(status_frame)
        url_display_frame.pack(fill=X, pady=5)

        ttk.Label(url_display_frame, text="Current URL:", width=15).pack(side=LEFT)
        self.current_url_var = tk.StringVar(value="Not browsing")
        url_display = ttk.Entry(
            url_display_frame,
            textvariable=self.current_url_var,
            state='readonly',
            width=70
        )
        url_display.pack(side=LEFT, fill=X, expand=YES, padx=5)

        # Action buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(pady=20)

        # Open Browser Button
        open_btn_kwargs: dict[str, Any] = {
            "text": "🌐 Open Browser for Login",
            "command": self._open_browser_for_login,
            "width": 30,
        }
        if USING_TTKBOOTSTRAP:
            open_btn_kwargs["bootstyle"] = "info"
            open_btn_kwargs["style"] = "Large.TButton"
        self.open_browser_btn = ttk.Button(button_frame, **open_btn_kwargs)
        self.open_browser_btn.pack(pady=5)

        # Stop Browser Button
        stop_browser_kwargs: dict[str, Any] = {
            "text": "⏹️ Stop Browser",
            "command": self._stop_browser,
            "width": 30,
            "state": DISABLED,
        }
        if USING_TTKBOOTSTRAP:
            stop_browser_kwargs["bootstyle"] = "danger"
            stop_browser_kwargs["style"] = "Large.TButton"
        self.stop_browser_btn = ttk.Button(button_frame, **stop_browser_kwargs)
        self.stop_browser_btn.pack(pady=5)

        # Save Session Button
        save_btn_kwargs: dict[str, Any] = {
            "text": "💾 Save Session (Keep Browser Alive)",
            "command": self._save_session_cookies,
            "width": 35,
            "state": DISABLED,
        }
        if USING_TTKBOOTSTRAP:
            save_btn_kwargs["bootstyle"] = "success"
            save_btn_kwargs["style"] = "Large.TButton"
        self.save_session_btn = ttk.Button(button_frame, **save_btn_kwargs)
        self.save_session_btn.pack(pady=5)

        # Status
        self.auth_status_var = tk.StringVar(value="")
        status_kwargs: dict[str, Any] = {
            "textvariable": self.auth_status_var,
            "font": ("Segoe UI", 10),
        }
        if USING_TTKBOOTSTRAP:
            status_kwargs["bootstyle"] = "secondary"
        status_label = ttk.Label(parent, **status_kwargs)
        status_label.pack(pady=10)

    def _update_browser_status(self, is_active: bool, message: str = "") -> None:
        """Update browser status indicator."""
        logger.info(f"Browser status update: active={is_active}, message={message}")
        
        self.browser_active = is_active
        
        if is_active:
            # Green indicator
            self.status_canvas.itemconfig(self.status_indicator, fill='#00ff00')
            self.browser_status_var.set("✅ Browser Loaded")
            logger.info("Browser status: ACTIVE (green indicator)")
        else:
            # Gray/Red indicator
            self.status_canvas.itemconfig(self.status_indicator, fill='gray')
            self.browser_status_var.set("⭕ Browser Inactive")
            logger.info("Browser status: INACTIVE (gray indicator)")
        
        if message:
            self.auth_status_var.set(message)

    def _start_url_monitoring(self) -> None:
        """Start monitoring browser URL in background thread."""
        logger.info("Starting URL monitoring thread")
        
        self.stop_url_monitor = False
        self.url_monitor_thread = threading.Thread(
            target=self._monitor_browser_url,
            daemon=True
        )
        self.url_monitor_thread.start()

    def _monitor_browser_url(self) -> None:
        """Monitor and update current browser URL."""
        logger.info("URL monitoring thread started")
        
        while not self.stop_url_monitor and self.selenium_service:
            try:
                if self.selenium_service.driver:
                    current_url = self.selenium_service.driver.current_url
                    if current_url != self.current_browser_url:
                        self.current_browser_url = current_url
                        logger.info(f"Browser navigated to: {current_url}")
                        # Update UI from main thread
                        self.root.after(0, lambda: self.current_url_var.set(current_url))
            except Exception as e:
                logger.error(f"Error monitoring URL: {e}")
            
            time.sleep(1)  # Check every second
        
        logger.info("URL monitoring thread stopped")

    def _stop_url_monitoring(self) -> None:
        """Stop URL monitoring thread."""
        logger.info("Stopping URL monitoring")
        self.stop_url_monitor = True
        if self.url_monitor_thread:
            self.url_monitor_thread.join(timeout=2)
        self.current_url_var.set("Not browsing")
        self.current_browser_url = ""

    def _create_saved_sessions_tab(self, parent: ttk.Frame) -> None:
        """Create saved sessions viewer."""
        logger.info("Creating saved sessions tab")
        
        # Refresh button
        refresh_kwargs: dict[str, Any] = {
            "text": "🔄 Refresh List",
            "command": self._refresh_saved_sessions,
        }
        if USING_TTKBOOTSTRAP:
            refresh_kwargs["bootstyle"] = "info-outline"
        refresh_btn = ttk.Button(parent, **refresh_kwargs)
        refresh_btn.pack(pady=(0, 10))

        # Sessions list
        self.sessions_listbox = ttk.Treeview(
            parent,
            columns=("name", "date", "domain"),
            show="headings",
            height=15,
        )

        self.sessions_listbox.heading("name", text="Session Name")
        self.sessions_listbox.heading("date", text="Created Date")
        self.sessions_listbox.heading("domain", text="Domain")

        self.sessions_listbox.column("name", width=200)
        self.sessions_listbox.column("date", width=200)
        self.sessions_listbox.column("domain", width=300)

        self.sessions_listbox.pack(fill=BOTH, expand=YES, pady=10)

        # Bind double-click event
        self.sessions_listbox.bind("<Double-Button-1>", self._on_session_double_click)
        logger.info("Double-click handler bound to sessions list")

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            parent,
            orient=VERTICAL,
            command=self.sessions_listbox.yview,
        )
        self.sessions_listbox.configure(yscrollcommand=scrollbar.set)

        # Action buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(pady=10)

        # Load Session Button (NEW)
        load_kwargs: dict[str, Any] = {
            "text": "🔄 Load Selected Session",
            "command": self._load_selected_session,
        }
        if USING_TTKBOOTSTRAP:
            load_kwargs["bootstyle"] = "success-outline"
        ttk.Button(btn_frame, **load_kwargs).pack(side=LEFT, padx=5)

        delete_kwargs: dict[str, Any] = {
            "text": "🗑️ Delete Selected",
            "command": self._delete_selected_session,
        }
        if USING_TTKBOOTSTRAP:
            delete_kwargs["bootstyle"] = "danger-outline"
        ttk.Button(btn_frame, **delete_kwargs).pack(side=LEFT, padx=5)

        open_folder_kwargs: dict[str, Any] = {
            "text": "📂 Open Cookies Folder",
            "command": self._open_cookies_folder,
        }
        if USING_TTKBOOTSTRAP:
            open_folder_kwargs["bootstyle"] = "secondary-outline"
        ttk.Button(btn_frame, **open_folder_kwargs).pack(side=LEFT, padx=5)

        self._refresh_saved_sessions()

    def _on_session_double_click(self, event: Any) -> None:
        """Handle double-click on session to load it."""
        logger.info("Session double-clicked")
        self._load_selected_session()

    def _load_selected_session(self) -> None:
        """Load selected session and reopen browser with cookies."""
        logger.info("Loading selected session")
        
        selection = self.sessions_listbox.selection()
        if not selection:
            logger.warning("No session selected for loading")
            messagebox.showwarning("Warning", "Please select a session to load")
            return

        item = self.sessions_listbox.item(selection[0])
        session_name = item["values"][0]
        logger.info(f"Loading session: {session_name}")

        cookie_file = Path("./cookies") / f"{session_name}.json"
        if not cookie_file.exists():
            logger.error(f"Cookie file not found: {cookie_file}")
            messagebox.showerror("Error", f"Cookie file not found: {session_name}")
            return

        try:
            # Load cookies to get domain
            with cookie_file.open("r", encoding="utf-8") as f:
                cookies = json.load(f)
            
            if not cookies:
                messagebox.showerror("Error", "Cookie file is empty")
                return

            # Get domain from first cookie
            domain = cookies[0].get("domain", "")
            if domain.startswith("."):
                domain = domain[1:]
            
            # Construct URL
            url = f"https://{domain}"
            logger.info(f"Reconstructed URL: {url}")

            # Close existing browser if open
            if self.selenium_service:
                logger.info("Closing existing browser session")
                self._stop_url_monitoring()
                self.selenium_service.stop_driver()
                self.selenium_service = None

            # Open new browser
            self.auth_status_var.set(f"Loading session '{session_name}'...")
            self.open_browser_btn.configure(state=DISABLED)
            self._update_browser_status(False, "Loading session...")

            # Create Selenium service
            selenium_config = SeleniumConfig(
                headless=False,
                window_size="1920,1080",
            )
            
            self.selenium_service = SeleniumService(selenium_config)
            self.selenium_service.start_driver()

            if not self.selenium_service.driver:
                raise RuntimeError("Failed to start Selenium driver")

            # Navigate to domain first
            logger.info(f"Navigating to: {url}")
            self.selenium_service.driver.get(url)
            
            # Load cookies
            logger.info(f"Loading cookies from: {cookie_file}")
            self.selenium_service.load_cookies(cookie_file)
            
            # Refresh to apply cookies
            self.selenium_service.driver.refresh()
            
            # Try to maximize
            try:
                self.selenium_service.driver.maximize_window()
            except Exception:
                pass

            # Update status
            self._update_browser_status(
                True,
                f"✅ Session '{session_name}' loaded! Continue browsing."
            )
            
            # Enable buttons
            self.save_session_btn.configure(state=NORMAL)
            self.stop_browser_btn.configure(state=NORMAL)
            
            # Start URL monitoring
            self._start_url_monitoring()
            
            # Update session name in form
            self.session_name_var.set(session_name)
            
            logger.info(f"Session '{session_name}' loaded successfully")
            messagebox.showinfo(
                "Success",
                f"Session '{session_name}' loaded!\n\nYou can now continue browsing."
            )

        except Exception as e:
            logger.error(f"Failed to load session: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to load session:\n{str(e)}")
            self._update_browser_status(False, "❌ Error loading session")
            self.open_browser_btn.configure(state=NORMAL)

    def _create_auth_help_tab(self, parent: ttk.Frame) -> None:
        """Create authentication help content."""
        help_text = """
🔐 Authentication Guide

Why Authenticate?
Many websites require login or block automated access. The Authentication Manager helps you:
• Log in to protected sites
• Save your session cookies
• Keep browser alive after saving
• Reload sessions anytime
• Crawl from your current browsing position

How It Works:
1. Enter the login URL (e.g., https://accounts.google.com)
2. Give your session a memorable name (e.g., google_work)
3. Click "Open Browser for Login" - a VISIBLE Chrome browser window opens
4. Watch the green indicator when browser loads ✅
5. Monitor the current URL as you navigate
6. Log in normally in the browser window (username, password, 2FA, etc.)
7. Complete any authentication steps in the visible browser
8. Browse to your TARGET PAGE where you want to start crawling
9. Click "Save Session (Keep Browser Alive)" - cookies saved, browser stays open!
10. Continue browsing or go to "Crawl Website" - URL is auto-synced!

Session Management:
• Double-click any saved session to reload it in the browser
• Click "Load Selected Session" button to manually load
• Browser reopens with your saved cookies
• Continue from where you left off

Supported Sites:
✅ Google (Gmail, Drive, Docs, etc.)
✅ Facebook
✅ LinkedIn
✅ Twitter/X
✅ GitHub (private repos)
✅ Any site with cookie-based authentication

Security:
⚠️ Cookie files contain authentication tokens
⚠️ Treat them like passwords - never share!
⚠️ Cookies are stored locally in ./cookies/ directory
⚠️ They expire based on the website's policy (typically 1-30 days)

Troubleshooting:
• "Browser won't open" → Install Chrome or Chromium
• "Can't see browser" → Check if it opened behind other windows
• "Session expired" → Delete old cookie file and re-authenticate
• "Access denied" → Site may require 2FA or IP changed
• Check webclone_gui.log for detailed error messages
        """.strip()

        text_widget = tk.Text(parent, wrap="word", height=25, font=("Segoe UI", 10))
        text_widget.insert("1.0", help_text)
        text_widget.configure(state="disabled")
        text_widget.pack(fill=BOTH, expand=YES)

    # ======================================================================
    # CRAWL PAGE
    # ======================================================================

    def _create_crawl_page(self) -> None:
        """Create the crawl configuration page."""
        logger.info("Creating crawl page")
        
        # If we have a saved session URL, sync it
        if self.saved_session_url:
            logger.info(f"Syncing saved session URL: {self.saved_session_url}")
        
        # Page title
        title = ttk.Label(
            self.content_frame,
            text="📥 Crawl Website",
            style="Title.TLabel",
        )
        title.pack(pady=(0, 10))

        subtitle_kwargs: dict[str, Any] = {
            "text": "Configure and execute website crawling",
            "style": "Subtitle.TLabel",
        }
        if USING_TTKBOOTSTRAP:
            subtitle_kwargs["bootstyle"] = "secondary"
        subtitle = ttk.Label(self.content_frame, **subtitle_kwargs)
        subtitle.pack(pady=(0, 20))

        # Basic configuration
        basic_frame = ttk.LabelFrame(
            self.content_frame,
            text="Basic Configuration",
            padding=20,
        )
        basic_frame.pack(fill=X, pady=10)

        # Target URL
        url_frame = ttk.Frame(basic_frame)
        url_frame.pack(fill=X, pady=5)

        ttk.Label(url_frame, text="Website URL:", width=15).pack(side=LEFT)
        
        # Use saved session URL if available, otherwise default
        default_url = self.saved_session_url if self.saved_session_url else "https://example.com"
        self.crawl_url_var = tk.StringVar(value=default_url)
        
        ttk.Entry(url_frame, textvariable=self.crawl_url_var, width=70).pack(
            side=LEFT,
            fill=X,
            expand=YES,
            padx=10,
        )

        # Sync button
        sync_btn_kwargs: dict[str, Any] = {
            "text": "🔄 Sync from Browser",
            "command": self._sync_url_from_browser,
        }
        if USING_TTKBOOTSTRAP:
            sync_btn_kwargs["bootstyle"] = "info-outline"
        ttk.Button(url_frame, **sync_btn_kwargs).pack(side=LEFT, padx=5)

        # Output directory
        output_frame = ttk.Frame(basic_frame)
        output_frame.pack(fill=X, pady=5)

        ttk.Label(output_frame, text="Output Directory:", width=15).pack(side=LEFT)
        self.output_dir_var = tk.StringVar(value="./website_mirror")
        ttk.Entry(output_frame, textvariable=self.output_dir_var, width=60).pack(
            side=LEFT,
            fill=X,
            expand=YES,
            padx=10,
        )
        browse_kwargs: dict[str, Any] = {
            "text": "Browse...",
            "command": self._browse_output_dir,
        }
        if USING_TTKBOOTSTRAP:
            browse_kwargs["bootstyle"] = "secondary-outline"
        ttk.Button(output_frame, **browse_kwargs).pack(side=LEFT)

        # Advanced settings
        advanced_frame = ttk.LabelFrame(
            self.content_frame,
            text="⚙️ Advanced Settings",
            padding=20,
        )
        advanced_frame.pack(fill=X, pady=10)

        # Crawling options
        crawl_opts_frame = ttk.Frame(advanced_frame)
        crawl_opts_frame.pack(fill=X, pady=5)

        left_col = ttk.Frame(crawl_opts_frame)
        left_col.pack(side=LEFT, fill=BOTH, expand=YES, padx=10)

        self.recursive_var = tk.BooleanVar(value=True)
        rec_kwargs: dict[str, Any] = {
            "text": "Recursive Crawl",
            "variable": self.recursive_var,
        }
        if USING_TTKBOOTSTRAP:
            rec_kwargs["bootstyle"] = "success-round-toggle"
        ttk.Checkbutton(left_col, **rec_kwargs).pack(anchor=W, pady=5)

        self.same_domain_var = tk.BooleanVar(value=True)
        same_kwargs: dict[str, Any] = {
            "text": "Same Domain Only",
            "variable": self.same_domain_var,
        }
        if USING_TTKBOOTSTRAP:
            same_kwargs["bootstyle"] = "success-round-toggle"
        ttk.Checkbutton(left_col, **same_kwargs).pack(anchor=W, pady=5)

        self.include_assets_var = tk.BooleanVar(value=True)
        assets_kwargs: dict[str, Any] = {
            "text": "Include Assets (CSS, JS, Images)",
            "variable": self.include_assets_var,
        }
        if USING_TTKBOOTSTRAP:
            assets_kwargs["bootstyle"] = "success-round-toggle"
        ttk.Checkbutton(left_col, **assets_kwargs).pack(anchor=W, pady=5)

        self.generate_pdf_var = tk.BooleanVar(value=False)
        pdf_kwargs: dict[str, Any] = {
            "text": "Generate PDFs",
            "variable": self.generate_pdf_var,
        }
        if USING_TTKBOOTSTRAP:
            pdf_kwargs["bootstyle"] = "success-round-toggle"
        ttk.Checkbutton(left_col, **pdf_kwargs).pack(anchor=W, pady=5)

        # Performance settings
        right_col = ttk.Frame(crawl_opts_frame)
        right_col.pack(side=LEFT, fill=BOTH, expand=YES, padx=10)

        # Workers
        workers_frame = ttk.Frame(right_col)
        workers_frame.pack(fill=X, pady=5)
        ttk.Label(workers_frame, text="Workers:", width=15).pack(side=LEFT)
        self.workers_var = tk.IntVar(value=5)
        ttk.Spinbox(
            workers_frame,
            from_=1,
            to=50,
            textvariable=self.workers_var,
            width=10,
        ).pack(side=LEFT)

        # Delay
        delay_frame = ttk.Frame(right_col)
        delay_frame.pack(fill=X, pady=5)
        ttk.Label(delay_frame, text="Delay (ms):", width=15).pack(side=LEFT)
        self.delay_var = tk.IntVar(value=100)
        ttk.Spinbox(
            delay_frame,
            from_=0,
            to=5000,
            increment=100,
            textvariable=self.delay_var,
            width=10,
        ).pack(side=LEFT)

        # Max depth
        depth_frame = ttk.Frame(right_col)
        depth_frame.pack(fill=X, pady=5)
        ttk.Label(depth_frame, text="Max Depth:", width=15).pack(side=LEFT)
        self.max_depth_var = tk.IntVar(value=0)
        ttk.Spinbox(
            depth_frame,
            from_=0,
            to=10,
            textvariable=self.max_depth_var,
            width=10,
        ).pack(side=LEFT)
        ttk.Label(depth_frame, text="(0 = unlimited)", font=("Segoe UI", 8)).pack(
            side=LEFT,
            padx=5,
        )

        # Max pages
        pages_frame = ttk.Frame(right_col)
        pages_frame.pack(fill=X, pady=5)
        ttk.Label(pages_frame, text="Max Pages:", width=15).pack(side=LEFT)
        self.max_pages_var = tk.IntVar(value=0)
        ttk.Spinbox(
            pages_frame,
            from_=0,
            to=10000,
            increment=10,
            textvariable=self.max_pages_var,
            width=10,
        ).pack(side=LEFT)
        ttk.Label(pages_frame, text="(0 = unlimited)", font=("Segoe UI", 8)).pack(
            side=LEFT,
            padx=5,
        )

        # Cookie file selection
        cookie_frame = ttk.LabelFrame(
            self.content_frame,
            text="🍪 Authentication (Optional)",
            padding=20,
        )
        cookie_frame.pack(fill=X, pady=10)

        self.cookie_file_var = tk.StringVar(value="None")
        cookie_select_frame = ttk.Frame(cookie_frame)
        cookie_select_frame.pack(fill=X)

        ttk.Label(cookie_select_frame, text="Cookie File:", width=15).pack(side=LEFT)
        self.cookie_combo = ttk.Combobox(
            cookie_select_frame,
            textvariable=self.cookie_file_var,
            values=["None"] + [p.stem for p in self.saved_cookies],
            state="readonly",
            width=50,
        )
        self.cookie_combo.pack(side=LEFT, fill=X, expand=YES, padx=10)
        self.cookie_combo.current(0)

        refresh_cookie_kwargs: dict[str, Any] = {
            "text": "🔄 Refresh",
            "command": self._refresh_cookie_list,
        }
        if USING_TTKBOOTSTRAP:
            refresh_cookie_kwargs["bootstyle"] = "secondary-outline"
        ttk.Button(cookie_select_frame, **refresh_cookie_kwargs).pack(side=LEFT)

        # Control buttons
        control_frame = ttk.Frame(self.content_frame)
        control_frame.pack(pady=20)

        start_btn_kwargs: dict[str, Any] = {
            "text": "▶️ Start Crawl",
            "command": self._start_crawl,
            "width": 25,
        }
        if USING_TTKBOOTSTRAP:
            start_btn_kwargs["bootstyle"] = "success"
            start_btn_kwargs["style"] = "Large.TButton"
        self.start_crawl_btn = ttk.Button(control_frame, **start_btn_kwargs)
        self.start_crawl_btn.pack(side=LEFT, padx=10)

        stop_btn_kwargs: dict[str, Any] = {
            "text": "⏹️ Stop Crawl",
            "command": self._stop_crawl,
            "width": 25,
            "state": DISABLED,
        }
        if USING_TTKBOOTSTRAP:
            stop_btn_kwargs["bootstyle"] = "danger"
            stop_btn_kwargs["style"] = "Large.TButton"
        self.stop_crawl_btn = ttk.Button(control_frame, **stop_btn_kwargs)
        self.stop_crawl_btn.pack(side=LEFT, padx=10)

        # Progress section
        progress_frame = ttk.LabelFrame(
            self.content_frame,
            text="📊 Progress",
            padding=20,
        )
        progress_frame.pack(fill=BOTH, expand=YES, pady=10)

        self.progress_var = tk.DoubleVar(value=0.0)
        progress_kwargs: dict[str, Any] = {
            "variable": self.progress_var,
            "mode": "determinate",
        }
        if USING_TTKBOOTSTRAP:
            progress_kwargs["bootstyle"] = "success-striped"
        self.progress_bar = ttk.Progressbar(progress_frame, **progress_kwargs)
        self.progress_bar.pack(fill=X, pady=10)

        # Status text
        self.crawl_status_var = tk.StringVar(value="Ready to start crawling...")
        status_kwargs: dict[str, Any] = {
            "textvariable": self.crawl_status_var,
            "font": ("Segoe UI", 10),
        }
        if USING_TTKBOOTSTRAP:
            status_kwargs["bootstyle"] = "secondary"
        status_label = ttk.Label(progress_frame, **status_kwargs)
        status_label.pack(pady=5)

        # Statistics
        stats_frame = ttk.Frame(progress_frame)
        stats_frame.pack(fill=X, pady=10)

        self.pages_crawled_var = tk.StringVar(value="Pages: 0")
        ttk.Label(
            stats_frame,
            textvariable=self.pages_crawled_var,
            font=("Segoe UI", 11, "bold"),
        ).pack(side=LEFT, padx=20)

        self.assets_downloaded_var = tk.StringVar(value="Assets: 0")
        ttk.Label(
            stats_frame,
            textvariable=self.assets_downloaded_var,
            font=("Segoe UI", 11, "bold"),
        ).pack(side=LEFT, padx=20)

        self.total_size_var = tk.StringVar(value="Size: 0 MB")
        ttk.Label(
            stats_frame,
            textvariable=self.total_size_var,
            font=("Segoe UI", 11, "bold"),
        ).pack(side=LEFT, padx=20)

        self.elapsed_time_var = tk.StringVar(value="Time: 0s")
        ttk.Label(
            stats_frame,
            textvariable=self.elapsed_time_var,
            font=("Segoe UI", 11, "bold"),
        ).pack(side=LEFT, padx=20)

    def _sync_url_from_browser(self) -> None:
        """Sync URL from current browser session."""
        logger.info("Syncing URL from browser")
        
        if self.selenium_service and self.selenium_service.driver:
            try:
                current_url = self.selenium_service.driver.current_url
                self.crawl_url_var.set(current_url)
                self.saved_session_url = current_url
                logger.info(f"URL synced from browser: {current_url}")
                messagebox.showinfo("Success", f"URL synced:\n{current_url}")
            except Exception as e:
                logger.error(f"Error syncing URL: {e}")
                messagebox.showerror("Error", f"Failed to sync URL:\n{str(e)}")
        else:
            messagebox.showwarning("Warning", "No active browser session")

    # ======================================================================
    # RESULTS PAGE
    # ======================================================================

    def _create_results_page(self) -> None:
        """Create the results and analytics page."""
        logger.info("Creating results page")
        
        # Page title
        title = ttk.Label(
            self.content_frame,
            text="📊 Results & Analytics",
            style="Title.TLabel",
        )
        title.pack(pady=(0, 10))

        if not self.crawl_metadata:
            # No results yet
            no_kwargs: dict[str, Any] = {
                "text": (
                    "No crawl results available yet.\n"
                    "Complete a crawl to see analytics here."
                ),
                "font": ("Segoe UI", 12),
                "justify": CENTER,
            }
            if USING_TTKBOOTSTRAP:
                no_kwargs["bootstyle"] = "secondary"
            no_results = ttk.Label(self.content_frame, **no_kwargs)
            no_results.pack(expand=YES)

            btn_kwargs: dict[str, Any] = {
                "text": "📥 Start a Crawl",
                "command": lambda: self._show_page("crawl"),
            }
            if USING_TTKBOOTSTRAP:
                btn_kwargs["bootstyle"] = "success"
                btn_kwargs["style"] = "Large.TButton"
            ttk.Button(self.content_frame, **btn_kwargs).pack(pady=20)
            return

        # Summary cards
        summary_frame = ttk.Frame(self.content_frame)
        summary_frame.pack(fill=X, pady=20)

        # Card 1: Pages
        card1 = ttk.LabelFrame(summary_frame, text="📄 Pages Crawled", padding=15)
        card1.pack(side=LEFT, fill=BOTH, expand=YES, padx=5)
        ttk.Label(
            card1,
            text=str(len(self.crawl_metadata.pages)),
            font=("Segoe UI", 32, "bold"),
        ).pack()

        # Card 2: Assets
        card2 = ttk.LabelFrame(summary_frame, text="📦 Assets Downloaded", padding=15)
        card2.pack(side=LEFT, fill=BOTH, expand=YES, padx=5)
        ttk.Label(
            card2,
            text=str(len(self.crawl_metadata.assets)),
            font=("Segoe UI", 32, "bold"),
        ).pack()

        # Card 3: Size
        card3 = ttk.LabelFrame(summary_frame, text="💾 Total Size", padding=15)
        card3.pack(side=LEFT, fill=BOTH, expand=YES, padx=5)
        total_mb = self.crawl_metadata.total_bytes / (1024 * 1024)
        ttk.Label(
            card3,
            text=f"{total_mb:.2f} MB",
            font=("Segoe UI", 32, "bold"),
        ).pack()

        # Card 4: Duration
        card4 = ttk.LabelFrame(summary_frame, text="⏱️ Duration", padding=15)
        card4.pack(side=LEFT, fill=BOTH, expand=YES, padx=5)
        duration_str = f"{self.crawl_metadata.duration_seconds:.1f}s"
        ttk.Label(
            card4,
            text=duration_str,
            font=("Segoe UI", 32, "bold"),
        ).pack()

        # Detailed results (notebook)
        notebook = ttk.Notebook(self.content_frame)
        notebook.pack(fill=BOTH, expand=YES, pady=20)

        # Tab 1: Pages
        pages_tab = ttk.Frame(notebook, padding=10)
        notebook.add(pages_tab, text="📄 Pages")
        self._create_pages_results_tab(pages_tab)

        # Tab 2: Assets
        assets_tab = ttk.Frame(notebook, padding=10)
        notebook.add(assets_tab, text="📦 Assets")
        self._create_assets_results_tab(assets_tab)

        # Tab 3: Export
        export_tab = ttk.Frame(notebook, padding=10)
        notebook.add(export_tab, text="💾 Export")
        self._create_export_tab(export_tab)

    def _create_pages_results_tab(self, parent: ttk.Frame) -> None:
        """Create pages results tab."""
        if not self.crawl_metadata:
            return

        # Treeview
        tree = ttk.Treeview(
            parent,
            columns=("url", "status", "depth", "links", "assets"),
            show="headings",
            height=20,
        )

        tree.heading("url", text="URL")
        tree.heading("status", text="Status")
        tree.heading("depth", text="Depth")
        tree.heading("links", text="Links")
        tree.heading("assets", text="Assets")

        tree.column("url", width=400)
        tree.column("status", width=80)
        tree.column("depth", width=80)
        tree.column("links", width=80)
        tree.column("assets", width=80)

        for page in self.crawl_metadata.pages:
            tree.insert(
                "",
                END,
                values=(
                    page.url,
                    page.status_code,
                    page.crawl_depth,
                    len(page.discovered_links),
                    page.assets_count,
                ),
            )

        tree.pack(fill=BOTH, expand=YES)

        # Scrollbar
        scrollbar = ttk.Scrollbar(parent, orient=VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

    def _create_assets_results_tab(self, parent: ttk.Frame) -> None:
        """Create assets results tab."""
        if not self.crawl_metadata:
            return

        # Group assets by type
        from collections import defaultdict

        assets_by_type: dict[str, int] = defaultdict(int)

        for asset in self.crawl_metadata.assets:
            assets_by_type[asset.resource_type.value] += 1

        # Display as table
        info_text = "Asset Distribution:\n\n"
        for asset_type, count in sorted(assets_by_type.items()):
            info_text += f"{asset_type.upper()}: {count}\n"

        text_widget = tk.Text(parent, wrap="word", height=20, font=("Consolas", 11))
        text_widget.insert("1.0", info_text)
        text_widget.configure(state="disabled")
        text_widget.pack(fill=BOTH, expand=YES)

    def _create_export_tab(self, parent: ttk.Frame) -> None:
        """Create export options tab."""
        info = ttk.Label(
            parent,
            text="Export your crawl results and view downloaded site",
            font=("Segoe UI", 11),
        )
        info.pack(pady=20)

        # View Downloaded Site Button (NEW)
        view_site_kwargs: dict[str, Any] = {
            "text": "🌐 View Downloaded Site",
            "command": self._view_downloaded_site,
            "width": 30,
        }
        if USING_TTKBOOTSTRAP:
            view_site_kwargs["bootstyle"] = "success"
            view_site_kwargs["style"] = "Large.TButton"
        ttk.Button(parent, **view_site_kwargs).pack(pady=10)

        export_json_kwargs: dict[str, Any] = {
            "text": "📥 Export as JSON",
            "command": self._export_json,
            "width": 30,
        }
        if USING_TTKBOOTSTRAP:
            export_json_kwargs["bootstyle"] = "primary"
        ttk.Button(parent, **export_json_kwargs).pack(pady=10)

        open_out_kwargs: dict[str, Any] = {
            "text": "📂 Open Output Directory",
            "command": self._open_output_directory,
            "width": 30,
        }
        if USING_TTKBOOTSTRAP:
            open_out_kwargs["bootstyle"] = "secondary"
        ttk.Button(parent, **open_out_kwargs).pack(pady=10)

    def _view_downloaded_site(self) -> None:
        """Open downloaded site in browser."""
        logger.info("Viewing downloaded site")
        
        output_dir = Path(self.output_dir_var.get())
        if not output_dir.exists():
            logger.warning("Output directory does not exist")
            messagebox.showwarning(
                "Warning",
                "Output directory does not exist yet. Complete a crawl first."
            )
            return

        # Look for index.html or first HTML file
        html_files = list(output_dir.glob("**/*.html"))
        
        if not html_files:
            logger.warning("No HTML files found in output directory")
            messagebox.showwarning(
                "Warning",
                "No HTML files found in output directory."
            )
            return

        # Try to find index.html first
        index_file = None
        for html_file in html_files:
            if html_file.name.lower() in ["index.html", "index.htm"]:
                index_file = html_file
                break
        
        # If no index, use first HTML file
        if not index_file:
            index_file = html_files[0]

        logger.info(f"Opening downloaded site: {index_file}")
        
        try:
            # Open in default browser
            webbrowser.open(f"file://{index_file.absolute()}")
            logger.info("Downloaded site opened in browser")
            messagebox.showinfo(
                "Success",
                f"Opened downloaded site:\n{index_file.name}"
            )
        except Exception as e:
            logger.error(f"Failed to open site: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to open site:\n{str(e)}")

    # ======================================================================
    # EVENT HANDLERS
    # ======================================================================

    def _load_saved_cookies(self) -> None:
        """Load list of saved cookie files."""
        logger.info("Loading saved cookies")
        cookies_dir = Path("./cookies")
        if cookies_dir.exists():
            self.saved_cookies = list(cookies_dir.glob("*.json"))
            logger.info(f"Found {len(self.saved_cookies)} saved cookie files")
        else:
            self.saved_cookies = []
            logger.info("No cookies directory found")

    def _refresh_cookie_list(self) -> None:
        """Refresh the cookie file dropdown."""
        logger.info("Refreshing cookie list")
        self._load_saved_cookies()
        if hasattr(self, "cookie_combo"):
            self.cookie_combo["values"] = ["None"] + [p.stem for p in self.saved_cookies]

    def _browse_output_dir(self) -> None:
        """Open directory browser."""
        logger.info("Opening directory browser")
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            logger.info(f"Selected output directory: {directory}")
            self.output_dir_var.set(directory)

    def _open_browser_for_login(self) -> None:
        """Open browser for manual login with VISIBLE WINDOW."""
        url = self.auth_url_var.get()
        logger.info(f"Opening VISIBLE browser for login to: {url}")

        if not url or not url.startswith("http"):
            logger.error("Invalid URL provided")
            messagebox.showerror("Error", "Please enter a valid URL")
            return

        self.auth_status_var.set(
            "Opening browser window... Please wait..."
        )
        self.open_browser_btn.configure(state=DISABLED)
        self._update_browser_status(False, "Initializing browser...")

        try:
            # Create Selenium config with HEADLESS=FALSE for visible browser
            logger.info("Creating Selenium service with VISIBLE browser")
            selenium_config = SeleniumConfig(
                headless=False,
                window_size="1920,1080",
            )
            
            self.selenium_service = SeleniumService(selenium_config)
            
            logger.info("Starting Selenium driver (VISIBLE MODE)")
            self.selenium_service.start_driver()

            if not self.selenium_service.driver:
                raise RuntimeError("Failed to start Selenium driver")

            # Navigate to URL
            logger.info(f"Navigating to URL: {url}")
            self.selenium_service.driver.get(url)
            
            # Try to bring window to front
            try:
                self.selenium_service.driver.maximize_window()
                logger.info("Browser window maximized")
            except Exception as e:
                logger.warning(f"Could not maximize window: {e}")

            # Update status to show browser is loaded
            self._update_browser_status(
                True,
                "✅ Browser window opened! Complete login and browse to target page."
            )
            
            # Enable buttons
            self.save_session_btn.configure(state=NORMAL)
            self.stop_browser_btn.configure(state=NORMAL)
            
            # Start URL monitoring
            self._start_url_monitoring()
            
            logger.info("VISIBLE browser opened successfully")

        except Exception as e:
            logger.error(f"Failed to open browser: {e}", exc_info=True)
            messagebox.showerror(
                "Error", 
                f"Failed to open browser:\n{str(e)}\n\nMake sure Chrome/Chromium is installed."
            )
            self._update_browser_status(False, "❌ Error opening browser")
            self.open_browser_btn.configure(state=NORMAL)

    def _stop_browser(self) -> None:
        """Stop/close the browser."""
        logger.info("Stopping browser")
        
        try:
            # Stop URL monitoring
            self._stop_url_monitoring()
            
            # Close browser
            if self.selenium_service:
                logger.info("Closing Selenium driver")
                self.selenium_service.stop_driver()
                self.selenium_service = None

            # Update UI
            self._update_browser_status(False, "Browser closed")
            self.stop_browser_btn.configure(state=DISABLED)
            self.save_session_btn.configure(state=DISABLED)
            self.open_browser_btn.configure(state=NORMAL)
            
            # Clear saved URL
            self.saved_session_url = ""
            
            logger.info("Browser stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping browser: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to stop browser:\n{str(e)}")

    def _save_session_cookies(self) -> None:
        """Save current session cookies WITHOUT closing browser."""
        logger.info("Saving session cookies (keeping browser alive)")
        
        if not self.selenium_service:
            logger.error("No browser session active")
            messagebox.showerror("Error", "No browser session active")
            return

        session_name = self.session_name_var.get()
        if not session_name:
            logger.error("No session name provided")
            messagebox.showerror("Error", "Please enter a session name")
            return

        try:
            # Create cookies directory
            cookies_dir = Path("./cookies")
            cookies_dir.mkdir(exist_ok=True)
            logger.info(f"Cookies directory: {cookies_dir}")

            # Save cookies
            cookie_file = cookies_dir / f"{session_name}.json"
            logger.info(f"Saving cookies to: {cookie_file}")
            self.selenium_service.save_cookies(cookie_file)

            # Save current URL for sync to crawl page
            if self.selenium_service.driver:
                self.saved_session_url = self.selenium_service.driver.current_url
                logger.info(f"Saved session URL: {self.saved_session_url}")

            # DON'T close browser - keep it alive!
            # DON'T stop URL monitoring - keep tracking!

            # Update UI
            self.auth_status_var.set(
                f"✅ Session '{session_name}' saved! Browser still active - continue browsing."
            )

            self._load_saved_cookies()

            logger.info(f"Session '{session_name}' saved successfully (browser kept alive)")

            messagebox.showinfo(
                "Success",
                (
                    f"Session '{session_name}' saved!\n\n"
                    "✅ Browser is still open - continue browsing!\n"
                    "✅ URL synced to Crawl page\n"
                    "✅ Ready to crawl from current page"
                ),
            )

        except Exception as e:
            logger.error(f"Failed to save session: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to save session:\n{str(e)}")

    def _refresh_saved_sessions(self) -> None:
        """Refresh the saved sessions list."""
        logger.info("Refreshing saved sessions list")
        self._load_saved_cookies()

        # Clear listbox
        for item in self.sessions_listbox.get_children():
            self.sessions_listbox.delete(item)

        # Populate with saved sessions
        for cookie_file in self.saved_cookies:
            try:
                with cookie_file.open("r", encoding="utf-8") as f:
                    cookies = json.load(f)

                # Get info
                name = cookie_file.stem
                date = datetime.fromtimestamp(cookie_file.stat().st_mtime).strftime(
                    "%Y-%m-%d %H:%M"
                )
                domain = cookies[0].get("domain", "Unknown") if cookies else "Unknown"

                self.sessions_listbox.insert(
                    "",
                    END,
                    values=(name, date, domain),
                )
                logger.info(f"Added session to list: {name}")
            except Exception as e:
                logger.error(f"Error loading session {cookie_file}: {e}")
                continue

    def _delete_selected_session(self) -> None:
        """Delete the selected session."""
        logger.info("Deleting selected session")
        selection = self.sessions_listbox.selection()
        if not selection:
            logger.warning("No session selected for deletion")
            messagebox.showwarning("Warning", "Please select a session to delete")
            return

        item = self.sessions_listbox.item(selection[0])
        session_name = item["values"][0]
        logger.info(f"Session to delete: {session_name}")

        if messagebox.askyesno(
            "Confirm Delete",
            f"Delete session '{session_name}'?\n\nThis cannot be undone.",
        ):
            cookie_file = Path("./cookies") / f"{session_name}.json"
            if cookie_file.exists():
                logger.info(f"Deleting cookie file: {cookie_file}")
                cookie_file.unlink()
                self._refresh_saved_sessions()
                messagebox.showinfo("Success", f"Session '{session_name}' deleted")
                logger.info(f"Session '{session_name}' deleted successfully")

    def _open_cookies_folder(self) -> None:
        """Open the cookies folder in file explorer."""
        logger.info("Opening cookies folder")
        cookies_dir = Path("./cookies").resolve()
        cookies_dir.mkdir(exist_ok=True)

        import platform
        import subprocess

        system = platform.system()
        logger.info(f"Opening folder on {system}")

        try:
            if system == "Windows":
                subprocess.run(["explorer", str(cookies_dir)])
            elif system == "Darwin":  # macOS
                subprocess.run(["open", str(cookies_dir)])
            else:  # Linux
                subprocess.run(["xdg-open", str(cookies_dir)])
            logger.info("Folder opened successfully")
        except Exception as e:
            logger.error(f"Failed to open folder: {e}", exc_info=True)

    def _start_crawl(self) -> None:
        """Start the crawl in a background thread."""
        url = self.crawl_url_var.get()
        logger.info(f"Starting crawl for URL: {url}")

        if not url or not url.startswith("http"):
            logger.error("Invalid crawl URL")
            messagebox.showerror("Error", "Please enter a valid URL")
            return

        # Disable start button, enable stop
        self.start_crawl_btn.configure(state=DISABLED)
        self.stop_crawl_btn.configure(state=NORMAL)
        self.is_crawling = True

        # Reset progress
        self.progress_var.set(0.0)
        self.crawl_status_var.set("Initializing crawl...")

        logger.info("Starting crawler thread")
        self.crawler_thread = threading.Thread(
            target=self._run_crawl_async,
            daemon=True,
        )
        self.crawler_thread.start()

        # Start progress updater
        self._update_progress()

    def _run_crawl_async(self) -> None:
        """Run the async crawl (executed in background thread)."""
        logger.info("Crawler thread started")
        
        try:
            # Create config
            logger.info("Creating crawl configuration")
            config = CrawlConfig(
                start_url=self.crawl_url_var.get(),
                output_dir=Path(self.output_dir_var.get()),
                recursive=self.recursive_var.get(),
                same_domain_only=self.same_domain_var.get(),
                max_depth=self.max_depth_var.get(),
                max_pages=self.max_pages_var.get(),
                include_assets=self.include_assets_var.get(),
                save_pdf=self.generate_pdf_var.get(),
                workers=self.workers_var.get(),
                delay_ms=self.delay_var.get(),
            )
            
            logger.info(f"Crawl config: {config}")

            # Load cookies if selected
            cookie_selection = self.cookie_file_var.get()
            if cookie_selection and cookie_selection != "None":
                cookie_file = Path("./cookies") / f"{cookie_selection}.json"
                if cookie_file.exists():
                    logger.info(f"Using cookie file: {cookie_file}")
                    config.cookie_file = cookie_file  # type: ignore[attr-defined]

            # Run crawl
            logger.info("Starting async crawl")
            
            async def crawl() -> None:
                async with AsyncCrawler(config) as crawler:
                    self.crawl_metadata = await crawler.crawl()

            asyncio.run(crawl())

            logger.info("Crawl completed successfully")
            self.crawl_status_var.set("✅ Crawl completed successfully!")
            messagebox.showinfo(
                "Success",
                "Crawl completed! View results in the Results tab.",
            )

        except Exception as e:
            logger.error(f"Crawl failed: {e}", exc_info=True)
            self.crawl_status_var.set(f"❌ Error: {str(e)}")
            messagebox.showerror("Error", f"Crawl failed:\n{str(e)}")

        finally:
            logger.info("Crawler thread finishing")
            self.is_crawling = False
            self.start_crawl_btn.configure(state=NORMAL)
            self.stop_crawl_btn.configure(state=DISABLED)

    def _update_progress(self) -> None:
        """Update progress indicators (called periodically)."""
        if not self.is_crawling:
            return

        # Update progress bar
        current = self.progress_var.get()
        if current < 90.0:
            self.progress_var.set(current + 1.0)

        # Schedule next update
        self.root.after(500, self._update_progress)

    def _stop_crawl(self) -> None:
        """Stop the current crawl."""
        logger.info("Stopping crawl")
        self.is_crawling = False
        self.crawl_status_var.set("⏹️ Crawl stopped by user")
        self.start_crawl_btn.configure(state=NORMAL)
        self.stop_crawl_btn.configure(state=DISABLED)

    def _export_json(self) -> None:
        """Export results as JSON."""
        logger.info("Exporting results as JSON")
        
        if not self.crawl_metadata:
            logger.warning("No crawl metadata to export")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )

        if filename:
            logger.info(f"Exporting to: {filename}")
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(self.crawl_metadata.model_dump(), f, indent=2, default=str)
                logger.info("Export successful")
                messagebox.showinfo("Success", f"Results exported to:\n{filename}")
            except Exception as e:
                logger.error(f"Export failed: {e}", exc_info=True)
                messagebox.showerror("Error", f"Export failed:\n{str(e)}")

    def _open_output_directory(self) -> None:
        """Open the output directory."""
        logger.info("Opening output directory")
        output_dir = Path(self.output_dir_var.get())
        
        if not output_dir.exists():
            logger.warning("Output directory does not exist")
            messagebox.showwarning(
                "Warning",
                "Output directory does not exist yet",
            )
            return

        import platform
        import subprocess

        system = platform.system()
        logger.info(f"Opening output directory on {system}")

        try:
            if system == "Windows":
                subprocess.run(["explorer", str(output_dir)])
            elif system == "Darwin":  # macOS
                subprocess.run(["open", str(output_dir)])
            else:  # Linux
                subprocess.run(["xdg-open", str(output_dir)])
            logger.info("Output directory opened")
        except Exception as e:
            logger.error(f"Failed to open directory: {e}", exc_info=True)

    def run(self) -> None:
        """Start the GUI application."""
        logger.info("Starting main GUI loop")
        try:
            self.root.mainloop()
        except Exception as e:
            logger.error(f"GUI error: {e}", exc_info=True)
        finally:
            logger.info("GUI application shutting down")
            # Cleanup
            if self.selenium_service:
                logger.info("Cleaning up Selenium service")
                self._stop_url_monitoring()
                self.selenium_service.stop_driver()


def main() -> None:
    """Entry point for the GUI application."""
    try:
        logger.info("Starting WebClone GUI application")
        app = WebCloneGUI()
        app.run()
        logger.info("Application exited normally")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()