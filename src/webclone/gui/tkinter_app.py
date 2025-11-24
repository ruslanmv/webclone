#!/usr/bin/env python3
"""
WebClone Enterprise GUI - Professional Tkinter Application

A world-class desktop interface for website cloning with:
- Modern, enterprise-grade design
- Intuitive navigation and workflow
- Real-time progress tracking
- Advanced authentication management
- Comprehensive results analytics

Author: Ruslan Magana
Website: ruslanmv.com
License: Apache 2.0
"""

import asyncio
import json
import threading
import time
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any, Callable, Optional

try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
    from ttkbootstrap.scrolled import ScrolledFrame
    from ttkbootstrap.toast import ToastNotification
except ImportError:
    import tkinter as tk
    from tkinter import ttk
    print("Warning: ttkbootstrap not available, using standard tkinter")

from webclone.core.crawler import AsyncCrawler
from webclone.models.config import CrawlConfig, SeleniumConfig
from webclone.models.metadata import CrawlMetadata
from webclone.services.selenium_service import SeleniumService


class WebCloneGUI:
    """Enterprise-grade Tkinter GUI for WebClone."""

    def __init__(self) -> None:
        """Initialize the GUI application."""
        # Try to use ttkbootstrap for modern theme
        try:
            self.root = ttk.Window(themename="cosmo")  # Modern blue theme
        except (NameError, AttributeError):
            import tkinter as tk
            self.root = tk.Tk()

        self.root.title("WebClone - Professional Website Cloning Engine")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)

        # Application state
        self.current_page = "home"
        self.crawler_thread: Optional[threading.Thread] = None
        self.is_crawling = False
        self.crawl_metadata: Optional[CrawlMetadata] = None
        self.selenium_service: Optional[SeleniumService] = None
        self.saved_cookies: list[Path] = []

        # Initialize UI
        self._setup_styles()
        self._create_layout()
        self._load_saved_cookies()
        self._show_page("home")

    def _setup_styles(self) -> None:
        """Configure custom styles for professional appearance."""
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

        except Exception:
            pass  # Fallback to default styles

    def _create_layout(self) -> None:
        """Create the main application layout."""
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=BOTH, expand=YES, padx=0, pady=0)

        # Sidebar (left)
        self._create_sidebar(main_container)

        # Content area (right)
        self.content_frame = ttk.Frame(main_container)
        self.content_frame.pack(side=LEFT, fill=BOTH, expand=YES, padx=20, pady=20)

    def _create_sidebar(self, parent: ttk.Frame) -> None:
        """Create navigation sidebar."""
        sidebar = ttk.Frame(parent, bootstyle="secondary", width=250)
        sidebar.pack(side=LEFT, fill=Y, padx=0, pady=0)
        sidebar.pack_propagate(False)

        # Logo/Title
        logo_frame = ttk.Frame(sidebar, bootstyle="secondary")
        logo_frame.pack(fill=X, padx=20, pady=30)

        title = ttk.Label(
            logo_frame,
            text="🌐 WebClone",
            font=("Segoe UI", 20, "bold"),
            bootstyle="inverse-secondary"
        )
        title.pack()

        subtitle = ttk.Label(
            logo_frame,
            text="Enterprise Edition",
            font=("Segoe UI", 9),
            bootstyle="inverse-secondary"
        )
        subtitle.pack()

        # Navigation buttons
        nav_frame = ttk.Frame(sidebar, bootstyle="secondary")
        nav_frame.pack(fill=BOTH, expand=YES, padx=10, pady=10)

        nav_buttons = [
            ("🏠 Home", "home", "primary"),
            ("🔐 Authentication", "auth", "info"),
            ("📥 Crawl Website", "crawl", "success"),
            ("📊 Results & Analytics", "results", "warning"),
        ]

        for text, page_id, bootstyle in nav_buttons:
            btn = ttk.Button(
                nav_frame,
                text=text,
                command=lambda p=page_id: self._show_page(p),
                bootstyle=f"{bootstyle}-outline",
                width=25
            )
            btn.pack(pady=5, fill=X)

        # Footer
        footer = ttk.Frame(sidebar, bootstyle="secondary")
        footer.pack(side=BOTTOM, fill=X, padx=20, pady=20)

        footer_text = ttk.Label(
            footer,
            text="© 2025 Ruslan Magana\nruslanmv.com",
            font=("Segoe UI", 8),
            bootstyle="inverse-secondary",
            justify=CENTER
        )
        footer_text.pack()

    def _show_page(self, page_id: str) -> None:
        """Switch to a different page."""
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

    # ============================================================================
    # HOME PAGE
    # ============================================================================

    def _create_home_page(self) -> None:
        """Create the home/dashboard page."""
        # Page title
        title = ttk.Label(
            self.content_frame,
            text="Welcome to WebClone Enterprise",
            style="Title.TLabel"
        )
        title.pack(pady=(0, 10))

        subtitle = ttk.Label(
            self.content_frame,
            text="Professional Website Cloning & Archival Engine",
            style="Subtitle.TLabel",
            bootstyle="secondary"
        )
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
            "Async-first architecture with concurrent downloads.\n10-100x faster than traditional crawlers.",
            "primary"
        ).pack(side=LEFT, fill=BOTH, expand=YES, padx=5)

        self._create_feature_card(
            row1,
            "🔐 Advanced Authentication",
            "Stealth mode bypasses bot detection.\nCookie-based persistent sessions.",
            "info"
        ).pack(side=LEFT, fill=BOTH, expand=YES, padx=5)

        # Row 2
        row2 = ttk.Frame(features_frame)
        row2.pack(fill=X, pady=10)

        self._create_feature_card(
            row2,
            "🎯 Smart Crawling",
            "Intelligent link discovery and asset extraction.\nRespects robots.txt and rate limits.",
            "success"
        ).pack(side=LEFT, fill=BOTH, expand=YES, padx=5)

        self._create_feature_card(
            row2,
            "📊 Comprehensive Analytics",
            "Detailed metrics and reports.\nReal-time progress tracking.",
            "warning"
        ).pack(side=LEFT, fill=BOTH, expand=YES, padx=5)

        # Quick start guide
        guide_frame = ttk.LabelFrame(
            self.content_frame,
            text="⚡ Quick Start Guide",
            padding=20
        )
        guide_frame.pack(fill=X, pady=30)

        steps = [
            "1️⃣ (Optional) Set up authentication for protected sites",
            "2️⃣ Navigate to 'Crawl Website' from the sidebar",
            "3️⃣ Enter target URL and configure settings",
            "4️⃣ Click 'Start Crawl' and watch real-time progress",
            "5️⃣ View results and analytics when complete"
        ]

        for step in steps:
            lbl = ttk.Label(guide_frame, text=step, font=("Segoe UI", 11))
            lbl.pack(anchor=W, pady=5)

        # Action buttons
        action_frame = ttk.Frame(self.content_frame)
        action_frame.pack(pady=20)

        ttk.Button(
            action_frame,
            text="🔐 Set Up Authentication",
            command=lambda: self._show_page("auth"),
            bootstyle="info",
            width=25
        ).pack(side=LEFT, padx=10)

        ttk.Button(
            action_frame,
            text="📥 Start Crawling Now",
            command=lambda: self._show_page("crawl"),
            bootstyle="success",
            width=25
        ).pack(side=LEFT, padx=10)

    def _create_feature_card(
        self,
        parent: ttk.Frame,
        title: str,
        description: str,
        bootstyle: str
    ) -> ttk.LabelFrame:
        """Create a feature card widget."""
        card = ttk.LabelFrame(
            parent,
            text=title,
            bootstyle=bootstyle,
            padding=15
        )

        desc = ttk.Label(
            card,
            text=description,
            wraplength=250,
            justify=LEFT
        )
        desc.pack()

        return card

    # ============================================================================
    # AUTHENTICATION PAGE
    # ============================================================================

    def _create_auth_page(self) -> None:
        """Create the authentication management page."""
        # Page title
        title = ttk.Label(
            self.content_frame,
            text="🔐 Authentication Manager",
            style="Title.TLabel"
        )
        title.pack(pady=(0, 10))

        subtitle = ttk.Label(
            self.content_frame,
            text="Manage authenticated sessions for protected websites",
            style="Subtitle.TLabel",
            bootstyle="secondary"
        )
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
        # Instructions
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill=X, pady=(0, 20))

        info = ttk.Label(
            info_frame,
            text="Authenticate to protected websites and save your session cookies for future use.",
            wraplength=800,
            font=("Segoe UI", 10)
        )
        info.pack()

        # Form
        form_frame = ttk.LabelFrame(parent, text="Login Configuration", padding=20)
        form_frame.pack(fill=X, pady=10)

        # Login URL
        url_frame = ttk.Frame(form_frame)
        url_frame.pack(fill=X, pady=10)

        ttk.Label(url_frame, text="Login URL:", width=20).pack(side=LEFT)
        self.auth_url_var = ttk.StringVar(value="https://accounts.google.com")
        url_entry = ttk.Entry(url_frame, textvariable=self.auth_url_var, width=60)
        url_entry.pack(side=LEFT, fill=X, expand=YES, padx=10)

        # Session Name
        name_frame = ttk.Frame(form_frame)
        name_frame.pack(fill=X, pady=10)

        ttk.Label(name_frame, text="Session Name:", width=20).pack(side=LEFT)
        self.session_name_var = ttk.StringVar(value="my_session")
        name_entry = ttk.Entry(name_frame, textvariable=self.session_name_var, width=60)
        name_entry.pack(side=LEFT, fill=X, expand=YES, padx=10)

        ttk.Label(
            form_frame,
            text="💡 Tip: Use descriptive names like 'google_work' or 'facebook_personal'",
            font=("Segoe UI", 9),
            bootstyle="info"
        ).pack(pady=5)

        # Action buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(pady=20)

        self.open_browser_btn = ttk.Button(
            button_frame,
            text="🌐 Open Browser for Login",
            command=self._open_browser_for_login,
            bootstyle="info",
            style="Large.TButton",
            width=30
        )
        self.open_browser_btn.pack(pady=5)

        self.save_session_btn = ttk.Button(
            button_frame,
            text="💾 Save Session & Cookies",
            command=self._save_session_cookies,
            bootstyle="success",
            style="Large.TButton",
            width=30,
            state=DISABLED
        )
        self.save_session_btn.pack(pady=5)

        # Status
        self.auth_status_var = ttk.StringVar(value="")
        status_label = ttk.Label(
            parent,
            textvariable=self.auth_status_var,
            font=("Segoe UI", 10),
            bootstyle="secondary"
        )
        status_label.pack(pady=10)

    def _create_saved_sessions_tab(self, parent: ttk.Frame) -> None:
        """Create saved sessions viewer."""
        # Refresh button
        refresh_btn = ttk.Button(
            parent,
            text="🔄 Refresh List",
            command=self._refresh_saved_sessions,
            bootstyle="info-outline"
        )
        refresh_btn.pack(pady=(0, 10))

        # Sessions list
        self.sessions_listbox = ttk.Treeview(
            parent,
            columns=("name", "date", "domain"),
            show="headings",
            height=15
        )

        self.sessions_listbox.heading("name", text="Session Name")
        self.sessions_listbox.heading("date", text="Created Date")
        self.sessions_listbox.heading("domain", text="Domain")

        self.sessions_listbox.column("name", width=200)
        self.sessions_listbox.column("date", width=200)
        self.sessions_listbox.column("domain", width=300)

        self.sessions_listbox.pack(fill=BOTH, expand=YES, pady=10)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            parent,
            orient=VERTICAL,
            command=self.sessions_listbox.yview
        )
        self.sessions_listbox.configure(yscrollcommand=scrollbar.set)

        # Action buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(pady=10)

        ttk.Button(
            btn_frame,
            text="🗑️ Delete Selected",
            command=self._delete_selected_session,
            bootstyle="danger-outline"
        ).pack(side=LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="📂 Open Cookies Folder",
            command=lambda: self._open_cookies_folder(),
            bootstyle="secondary-outline"
        ).pack(side=LEFT, padx=5)

        self._refresh_saved_sessions()

    def _create_auth_help_tab(self, parent: ttk.Frame) -> None:
        """Create authentication help content."""
        help_text = """
🔐 Authentication Guide

Why Authenticate?
Many websites require login or block automated access. The Authentication Manager helps you:
• Log in to protected sites
• Save your session cookies
• Reuse authentication for future crawls

How It Works:
1. Enter the login URL (e.g., https://accounts.google.com)
2. Give your session a memorable name (e.g., google_work)
3. Click "Open Browser for Login" - a real Chrome browser opens
4. Log in normally (username, password, 2FA, etc.)
5. Click "Save Session & Cookies" - your session is saved
6. Use saved cookies in future crawls!

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
• "Session expired" → Delete old cookie file and re-authenticate
• "Access denied" → Site may require 2FA or IP changed
        """

        text_widget = ttk.Text(parent, wrap=WORD, height=25, font=("Segoe UI", 10))
        text_widget.insert("1.0", help_text.strip())
        text_widget.configure(state=DISABLED)
        text_widget.pack(fill=BOTH, expand=YES)

    # ============================================================================
    # CRAWL PAGE
    # ============================================================================

    def _create_crawl_page(self) -> None:
        """Create the crawl configuration page."""
        # Page title
        title = ttk.Label(
            self.content_frame,
            text="📥 Crawl Website",
            style="Title.TLabel"
        )
        title.pack(pady=(0, 10))

        subtitle = ttk.Label(
            self.content_frame,
            text="Configure and execute website crawling",
            style="Subtitle.TLabel",
            bootstyle="secondary"
        )
        subtitle.pack(pady=(0, 20))

        # Basic configuration
        basic_frame = ttk.LabelFrame(
            self.content_frame,
            text="Basic Configuration",
            padding=20
        )
        basic_frame.pack(fill=X, pady=10)

        # Target URL
        url_frame = ttk.Frame(basic_frame)
        url_frame.pack(fill=X, pady=5)

        ttk.Label(url_frame, text="Website URL:", width=15).pack(side=LEFT)
        self.crawl_url_var = ttk.StringVar(value="https://example.com")
        ttk.Entry(url_frame, textvariable=self.crawl_url_var, width=70).pack(
            side=LEFT, fill=X, expand=YES, padx=10
        )

        # Output directory
        output_frame = ttk.Frame(basic_frame)
        output_frame.pack(fill=X, pady=5)

        ttk.Label(output_frame, text="Output Directory:", width=15).pack(side=LEFT)
        self.output_dir_var = ttk.StringVar(value="./website_mirror")
        ttk.Entry(output_frame, textvariable=self.output_dir_var, width=60).pack(
            side=LEFT, fill=X, expand=YES, padx=10
        )
        ttk.Button(
            output_frame,
            text="Browse...",
            command=self._browse_output_dir,
            bootstyle="secondary-outline"
        ).pack(side=LEFT)

        # Advanced settings (collapsible)
        advanced_frame = ttk.LabelFrame(
            self.content_frame,
            text="⚙️ Advanced Settings",
            padding=20
        )
        advanced_frame.pack(fill=X, pady=10)

        # Crawling options
        crawl_opts_frame = ttk.Frame(advanced_frame)
        crawl_opts_frame.pack(fill=X, pady=5)

        left_col = ttk.Frame(crawl_opts_frame)
        left_col.pack(side=LEFT, fill=BOTH, expand=YES, padx=10)

        self.recursive_var = ttk.BooleanVar(value=True)
        ttk.Checkbutton(
            left_col,
            text="Recursive Crawl",
            variable=self.recursive_var,
            bootstyle="success-round-toggle"
        ).pack(anchor=W, pady=5)

        self.same_domain_var = ttk.BooleanVar(value=True)
        ttk.Checkbutton(
            left_col,
            text="Same Domain Only",
            variable=self.same_domain_var,
            bootstyle="success-round-toggle"
        ).pack(anchor=W, pady=5)

        self.include_assets_var = ttk.BooleanVar(value=True)
        ttk.Checkbutton(
            left_col,
            text="Include Assets (CSS, JS, Images)",
            variable=self.include_assets_var,
            bootstyle="success-round-toggle"
        ).pack(anchor=W, pady=5)

        self.generate_pdf_var = ttk.BooleanVar(value=False)
        ttk.Checkbutton(
            left_col,
            text="Generate PDFs",
            variable=self.generate_pdf_var,
            bootstyle="success-round-toggle"
        ).pack(anchor=W, pady=5)

        # Performance settings
        right_col = ttk.Frame(crawl_opts_frame)
        right_col.pack(side=LEFT, fill=BOTH, expand=YES, padx=10)

        # Workers
        workers_frame = ttk.Frame(right_col)
        workers_frame.pack(fill=X, pady=5)
        ttk.Label(workers_frame, text="Workers:", width=15).pack(side=LEFT)
        self.workers_var = ttk.IntVar(value=5)
        ttk.Spinbox(
            workers_frame,
            from_=1,
            to=50,
            textvariable=self.workers_var,
            width=10
        ).pack(side=LEFT)

        # Delay
        delay_frame = ttk.Frame(right_col)
        delay_frame.pack(fill=X, pady=5)
        ttk.Label(delay_frame, text="Delay (ms):", width=15).pack(side=LEFT)
        self.delay_var = ttk.IntVar(value=100)
        ttk.Spinbox(
            delay_frame,
            from_=0,
            to=5000,
            increment=100,
            textvariable=self.delay_var,
            width=10
        ).pack(side=LEFT)

        # Max depth
        depth_frame = ttk.Frame(right_col)
        depth_frame.pack(fill=X, pady=5)
        ttk.Label(depth_frame, text="Max Depth:", width=15).pack(side=LEFT)
        self.max_depth_var = ttk.IntVar(value=0)
        ttk.Spinbox(
            depth_frame,
            from_=0,
            to=10,
            textvariable=self.max_depth_var,
            width=10
        ).pack(side=LEFT)
        ttk.Label(depth_frame, text="(0 = unlimited)", font=("Segoe UI", 8)).pack(
            side=LEFT, padx=5
        )

        # Max pages
        pages_frame = ttk.Frame(right_col)
        pages_frame.pack(fill=X, pady=5)
        ttk.Label(pages_frame, text="Max Pages:", width=15).pack(side=LEFT)
        self.max_pages_var = ttk.IntVar(value=0)
        ttk.Spinbox(
            pages_frame,
            from_=0,
            to=10000,
            increment=10,
            textvariable=self.max_pages_var,
            width=10
        ).pack(side=LEFT)
        ttk.Label(pages_frame, text="(0 = unlimited)", font=("Segoe UI", 8)).pack(
            side=LEFT, padx=5
        )

        # Cookie file selection
        cookie_frame = ttk.LabelFrame(
            self.content_frame,
            text="🍪 Authentication (Optional)",
            padding=20
        )
        cookie_frame.pack(fill=X, pady=10)

        self.cookie_file_var = ttk.StringVar(value="None")
        cookie_select_frame = ttk.Frame(cookie_frame)
        cookie_select_frame.pack(fill=X)

        ttk.Label(cookie_select_frame, text="Cookie File:", width=15).pack(side=LEFT)
        self.cookie_combo = ttk.Combobox(
            cookie_select_frame,
            textvariable=self.cookie_file_var,
            values=["None"] + [p.stem for p in self.saved_cookies],
            state="readonly",
            width=50
        )
        self.cookie_combo.pack(side=LEFT, fill=X, expand=YES, padx=10)
        self.cookie_combo.current(0)

        ttk.Button(
            cookie_select_frame,
            text="🔄 Refresh",
            command=self._refresh_cookie_list,
            bootstyle="secondary-outline"
        ).pack(side=LEFT)

        # Control buttons
        control_frame = ttk.Frame(self.content_frame)
        control_frame.pack(pady=20)

        self.start_crawl_btn = ttk.Button(
            control_frame,
            text="▶️ Start Crawl",
            command=self._start_crawl,
            bootstyle="success",
            style="Large.TButton",
            width=25
        )
        self.start_crawl_btn.pack(side=LEFT, padx=10)

        self.stop_crawl_btn = ttk.Button(
            control_frame,
            text="⏹️ Stop Crawl",
            command=self._stop_crawl,
            bootstyle="danger",
            style="Large.TButton",
            width=25,
            state=DISABLED
        )
        self.stop_crawl_btn.pack(side=LEFT, padx=10)

        # Progress section
        progress_frame = ttk.LabelFrame(
            self.content_frame,
            text="📊 Progress",
            padding=20
        )
        progress_frame.pack(fill=BOTH, expand=YES, pady=10)

        self.progress_var = ttk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            bootstyle="success-striped",
            mode="determinate"
        )
        self.progress_bar.pack(fill=X, pady=10)

        # Status text
        self.crawl_status_var = ttk.StringVar(value="Ready to start crawling...")
        status_label = ttk.Label(
            progress_frame,
            textvariable=self.crawl_status_var,
            font=("Segoe UI", 10),
            bootstyle="secondary"
        )
        status_label.pack(pady=5)

        # Statistics
        stats_frame = ttk.Frame(progress_frame)
        stats_frame.pack(fill=X, pady=10)

        self.pages_crawled_var = ttk.StringVar(value="Pages: 0")
        ttk.Label(
            stats_frame,
            textvariable=self.pages_crawled_var,
            font=("Segoe UI", 11, "bold")
        ).pack(side=LEFT, padx=20)

        self.assets_downloaded_var = ttk.StringVar(value="Assets: 0")
        ttk.Label(
            stats_frame,
            textvariable=self.assets_downloaded_var,
            font=("Segoe UI", 11, "bold")
        ).pack(side=LEFT, padx=20)

        self.total_size_var = ttk.StringVar(value="Size: 0 MB")
        ttk.Label(
            stats_frame,
            textvariable=self.total_size_var,
            font=("Segoe UI", 11, "bold")
        ).pack(side=LEFT, padx=20)

        self.elapsed_time_var = ttk.StringVar(value="Time: 0s")
        ttk.Label(
            stats_frame,
            textvariable=self.elapsed_time_var,
            font=("Segoe UI", 11, "bold")
        ).pack(side=LEFT, padx=20)

    # ============================================================================
    # RESULTS PAGE
    # ============================================================================

    def _create_results_page(self) -> None:
        """Create the results and analytics page."""
        # Page title
        title = ttk.Label(
            self.content_frame,
            text="📊 Results & Analytics",
            style="Title.TLabel"
        )
        title.pack(pady=(0, 10))

        if not self.crawl_metadata:
            # No results yet
            no_results = ttk.Label(
                self.content_frame,
                text="No crawl results available yet.\nComplete a crawl to see analytics here.",
                font=("Segoe UI", 12),
                bootstyle="secondary",
                justify=CENTER
            )
            no_results.pack(expand=YES)

            ttk.Button(
                self.content_frame,
                text="📥 Start a Crawl",
                command=lambda: self._show_page("crawl"),
                bootstyle="success",
                style="Large.TButton"
            ).pack(pady=20)
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
            bootstyle="primary"
        ).pack()

        # Card 2: Assets
        card2 = ttk.LabelFrame(summary_frame, text="📦 Assets Downloaded", padding=15)
        card2.pack(side=LEFT, fill=BOTH, expand=YES, padx=5)
        ttk.Label(
            card2,
            text=str(len(self.crawl_metadata.assets)),
            font=("Segoe UI", 32, "bold"),
            bootstyle="info"
        ).pack()

        # Card 3: Size
        card3 = ttk.LabelFrame(summary_frame, text="💾 Total Size", padding=15)
        card3.pack(side=LEFT, fill=BOTH, expand=YES, padx=5)
        total_mb = self.crawl_metadata.total_size_bytes / (1024 * 1024)
        ttk.Label(
            card3,
            text=f"{total_mb:.2f} MB",
            font=("Segoe UI", 32, "bold"),
            bootstyle="success"
        ).pack()

        # Card 4: Duration
        card4 = ttk.LabelFrame(summary_frame, text="⏱️ Duration", padding=15)
        card4.pack(side=LEFT, fill=BOTH, expand=YES, padx=5)
        duration_str = f"{self.crawl_metadata.duration_seconds:.1f}s"
        ttk.Label(
            card4,
            text=duration_str,
            font=("Segoe UI", 32, "bold"),
            bootstyle="warning"
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
            height=20
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
                    page.depth,
                    len(page.links_found),
                    len(page.assets_found)
                )
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

        text_widget = ttk.Text(parent, wrap=WORD, height=20, font=("Consolas", 11))
        text_widget.insert("1.0", info_text)
        text_widget.configure(state=DISABLED)
        text_widget.pack(fill=BOTH, expand=YES)

    def _create_export_tab(self, parent: ttk.Frame) -> None:
        """Create export options tab."""
        info = ttk.Label(
            parent,
            text="Export your crawl results in various formats",
            font=("Segoe UI", 11)
        )
        info.pack(pady=20)

        ttk.Button(
            parent,
            text="📥 Export as JSON",
            command=self._export_json,
            bootstyle="primary",
            width=30
        ).pack(pady=10)

        ttk.Button(
            parent,
            text="📂 Open Output Directory",
            command=self._open_output_directory,
            bootstyle="secondary",
            width=30
        ).pack(pady=10)

    # ============================================================================
    # EVENT HANDLERS
    # ============================================================================

    def _load_saved_cookies(self) -> None:
        """Load list of saved cookie files."""
        cookies_dir = Path("./cookies")
        if cookies_dir.exists():
            self.saved_cookies = list(cookies_dir.glob("*.json"))
        else:
            self.saved_cookies = []

    def _refresh_cookie_list(self) -> None:
        """Refresh the cookie file dropdown."""
        self._load_saved_cookies()
        if hasattr(self, "cookie_combo"):
            self.cookie_combo["values"] = ["None"] + [p.stem for p in self.saved_cookies]

    def _browse_output_dir(self) -> None:
        """Open directory browser."""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir_var.set(directory)

    def _open_browser_for_login(self) -> None:
        """Open browser for manual login."""
        url = self.auth_url_var.get()

        if not url or not url.startswith("http"):
            messagebox.showerror("Error", "Please enter a valid URL")
            return

        self.auth_status_var.set("Opening browser... Please log in and complete authentication.")
        self.open_browser_btn.configure(state=DISABLED)

        try:
            # Create Selenium service
            selenium_config = SeleniumConfig()
            self.selenium_service = SeleniumService(selenium_config)
            self.selenium_service.start_driver()

            # Navigate to URL
            self.selenium_service.driver.get(url)

            self.auth_status_var.set(
                "✅ Browser opened! Log in, then click 'Save Session & Cookies'"
            )
            self.save_session_btn.configure(state=NORMAL)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open browser:\n{str(e)}")
            self.auth_status_var.set("❌ Error opening browser")
            self.open_browser_btn.configure(state=NORMAL)

    def _save_session_cookies(self) -> None:
        """Save current session cookies."""
        if not self.selenium_service:
            messagebox.showerror("Error", "No browser session active")
            return

        session_name = self.session_name_var.get()
        if not session_name:
            messagebox.showerror("Error", "Please enter a session name")
            return

        try:
            # Create cookies directory
            cookies_dir = Path("./cookies")
            cookies_dir.mkdir(exist_ok=True)

            # Save cookies
            cookie_file = cookies_dir / f"{session_name}.json"
            self.selenium_service.save_cookies(cookie_file)

            # Close browser
            self.selenium_service.stop_driver()
            self.selenium_service = None

            self.auth_status_var.set(f"✅ Session '{session_name}' saved successfully!")
            self.save_session_btn.configure(state=DISABLED)
            self.open_browser_btn.configure(state=NORMAL)

            self._load_saved_cookies()

            messagebox.showinfo(
                "Success",
                f"Session '{session_name}' saved!\n\nYou can now use these cookies in your crawls."
            )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save session:\n{str(e)}")

    def _refresh_saved_sessions(self) -> None:
        """Refresh the saved sessions list."""
        self._load_saved_cookies()

        # Clear listbox
        for item in self.sessions_listbox.get_children():
            self.sessions_listbox.delete(item)

        # Populate with saved sessions
        for cookie_file in self.saved_cookies:
            try:
                with open(cookie_file, "r") as f:
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
                    values=(name, date, domain)
                )
            except Exception:
                continue

    def _delete_selected_session(self) -> None:
        """Delete the selected session."""
        selection = self.sessions_listbox.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a session to delete")
            return

        item = self.sessions_listbox.item(selection[0])
        session_name = item["values"][0]

        if messagebox.askyesno(
            "Confirm Delete",
            f"Delete session '{session_name}'?\n\nThis cannot be undone."
        ):
            cookie_file = Path("./cookies") / f"{session_name}.json"
            if cookie_file.exists():
                cookie_file.unlink()
                self._refresh_saved_sessions()
                messagebox.showinfo("Success", f"Session '{session_name}' deleted")

    def _open_cookies_folder(self) -> None:
        """Open the cookies folder in file explorer."""
        cookies_dir = Path("./cookies").resolve()
        cookies_dir.mkdir(exist_ok=True)

        import platform
        import subprocess

        if platform.system() == "Windows":
            subprocess.run(["explorer", str(cookies_dir)])
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", str(cookies_dir)])
        else:  # Linux
            subprocess.run(["xdg-open", str(cookies_dir)])

    def _start_crawl(self) -> None:
        """Start the crawl in a background thread."""
        url = self.crawl_url_var.get()

        if not url or not url.startswith("http"):
            messagebox.showerror("Error", "Please enter a valid URL")
            return

        # Disable start button, enable stop
        self.start_crawl_btn.configure(state=DISABLED)
        self.stop_crawl_btn.configure(state=NORMAL)
        self.is_crawling = True

        # Reset progress
        self.progress_var.set(0)
        self.crawl_status_var.set("Initializing crawl...")

        # Start in background thread
        self.crawler_thread = threading.Thread(target=self._run_crawl_async, daemon=True)
        self.crawler_thread.start()

        # Start progress updater
        self._update_progress()

    def _run_crawl_async(self) -> None:
        """Run the async crawl (executed in background thread)."""
        try:
            # Create config
            config = CrawlConfig(
                start_url=self.crawl_url_var.get(),
                output_dir=Path(self.output_dir_var.get()),
                recursive=self.recursive_var.get(),
                same_domain_only=self.same_domain_var.get(),
                max_depth=self.max_depth_var.get() if self.max_depth_var.get() > 0 else None,
                max_pages=self.max_pages_var.get() if self.max_pages_var.get() > 0 else None,
                include_assets=self.include_assets_var.get(),
                generate_pdf=self.generate_pdf_var.get(),
                workers=self.workers_var.get(),
                delay_ms=self.delay_var.get(),
            )

            # Load cookies if selected
            cookie_selection = self.cookie_file_var.get()
            if cookie_selection and cookie_selection != "None":
                cookie_file = Path("./cookies") / f"{cookie_selection}.json"
                if cookie_file.exists():
                    config.cookie_file = cookie_file

            # Run crawl
            async def crawl() -> None:
                async with AsyncCrawler(config) as crawler:
                    self.crawl_metadata = await crawler.crawl()

            # Run in event loop
            asyncio.run(crawl())

            self.crawl_status_var.set("✅ Crawl completed successfully!")
            messagebox.showinfo("Success", "Crawl completed! View results in the Results tab.")

        except Exception as e:
            self.crawl_status_var.set(f"❌ Error: {str(e)}")
            messagebox.showerror("Error", f"Crawl failed:\n{str(e)}")

        finally:
            self.is_crawling = False
            self.start_crawl_btn.configure(state=NORMAL)
            self.stop_crawl_btn.configure(state=DISABLED)

    def _update_progress(self) -> None:
        """Update progress indicators (called periodically)."""
        if not self.is_crawling:
            return

        # Update progress bar (simulate progress)
        current = self.progress_var.get()
        if current < 90:
            self.progress_var.set(current + 1)

        # Schedule next update
        self.root.after(500, self._update_progress)

    def _stop_crawl(self) -> None:
        """Stop the current crawl."""
        self.is_crawling = False
        self.crawl_status_var.set("⏹️ Crawl stopped by user")
        self.start_crawl_btn.configure(state=NORMAL)
        self.stop_crawl_btn.configure(state=DISABLED)

    def _export_json(self) -> None:
        """Export results as JSON."""
        if not self.crawl_metadata:
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            with open(filename, "w") as f:
                json.dump(self.crawl_metadata.model_dump(), f, indent=2, default=str)
            messagebox.showinfo("Success", f"Results exported to:\n{filename}")

    def _open_output_directory(self) -> None:
        """Open the output directory."""
        output_dir = Path(self.output_dir_var.get())
        if not output_dir.exists():
            messagebox.showwarning("Warning", "Output directory does not exist yet")
            return

        import platform
        import subprocess

        if platform.system() == "Windows":
            subprocess.run(["explorer", str(output_dir)])
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", str(output_dir)])
        else:  # Linux
            subprocess.run(["xdg-open", str(output_dir)])

    def run(self) -> None:
        """Start the GUI application."""
        self.root.mainloop()


def main() -> None:
    """Entry point for the GUI application."""
    app = WebCloneGUI()
    app.run()


if __name__ == "__main__":
    main()
