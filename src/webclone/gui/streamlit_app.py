"""
Modern Streamlit Web UI for WebClone

A professional, production-ready web interface for website cloning and archival.
Features cookie-based authentication, real-time progress tracking, and beautiful design.

Author: Ruslan Magana
Website: ruslanmv.com
"""

import asyncio
import json
from pathlib import Path
from typing import Optional

import streamlit as st
from streamlit_option_menu import option_menu

from webclone import __version__
from webclone.core.crawler import AsyncCrawler
from webclone.models.config import CrawlConfig, SeleniumConfig
from webclone.services.selenium_service import SeleniumService


# Page configuration
st.set_page_config(
    page_title="WebClone - Professional Website Cloning",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for professional look
st.markdown(
    """
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .feature-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def initialize_session_state() -> None:
    """Initialize Streamlit session state variables."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "cookies_saved" not in st.session_state:
        st.session_state.cookies_saved = False
    if "cookie_file" not in st.session_state:
        st.session_state.cookie_file = None
    if "selenium_service" not in st.session_state:
        st.session_state.selenium_service = None
    if "crawl_results" not in st.session_state:
        st.session_state.crawl_results = []


def show_header() -> None:
    """Display the application header."""
    st.markdown('<h1 class="main-header">🌐 WebClone</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="subtitle">Professional Website Cloning & Archival Platform</p>',
        unsafe_allow_html=True,
    )
    st.markdown(f"**Version:** {__version__} | **Author:** Ruslan Magana | **License:** Apache 2.0")
    st.markdown("---")


def page_home() -> None:
    """Home page with welcome and quick start."""
    show_header()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
            <div class="feature-card">
            <h3>⚡ Blazingly Fast</h3>
            <p>Async-first architecture with 5-50 concurrent workers for maximum performance.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="feature-card">
            <h3>🔐 Stealth Mode</h3>
            <p>Bypass bot detection and handle authentication with advanced anti-detection techniques.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
            <div class="feature-card">
            <h3>🎨 Beautiful UI</h3>
            <p>Modern, professional interface with real-time progress tracking and analytics.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("## 🚀 Quick Start Guide")

    st.markdown(
        """
        ### How to Use WebClone:

        1. **🔐 Authenticate** (Optional)
           - For sites requiring login, go to the "Authentication" tab
           - Open browser, log in manually, save your session
           - Cookies will be reused for future crawls

        2. **🌐 Configure Crawl**
           - Go to the "Crawl Website" tab
           - Enter the URL you want to clone
           - Adjust settings (workers, depth, etc.)

        3. **▶️ Start Crawling**
           - Click "Start Crawl"
           - Monitor real-time progress
           - Download results when complete

        4. **📊 View Results**
           - Check the "Results" tab for statistics
           - Download reports and archived content
        """
    )

    st.markdown("---")
    st.markdown(
        """
        ### ✨ Key Features:
        - ✅ Async concurrent downloads (10-100x faster)
        - ✅ Full JavaScript rendering with Selenium
        - ✅ Cookie-based authentication
        - ✅ GCM/FCM error elimination
        - ✅ Rate limit detection
        - ✅ PDF and screenshot generation
        - ✅ Comprehensive metadata reports
        """
    )


def page_authenticate() -> None:
    """Authentication page for manual login and cookie management."""
    show_header()

    st.markdown("## 🔐 Authentication & Session Management")

    st.markdown(
        """
        <div class="info-box">
        <strong>💡 Why Authenticate?</strong><br>
        For sites that require login (Google, Facebook, LinkedIn, etc.), you need to authenticate first.
        WebClone will save your session cookies and reuse them for automated crawling.
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3 = st.tabs(["🆕 New Login", "📂 Load Cookies", "ℹ️ Help"])

    with tab1:
        st.markdown("### Manual Login Session")

        login_url = st.text_input(
            "Login URL",
            value="https://accounts.google.com",
            help="Enter the login page URL",
        )

        cookie_name = st.text_input(
            "Session Name",
            value="my_session",
            help="A name to identify this session (e.g., 'google_auth', 'facebook_session')",
        )

        if st.button("🌐 Open Browser for Login", type="primary", use_container_width=True):
            if not login_url.startswith(("http://", "https://")):
                st.error("❌ Invalid URL. Must start with http:// or https://")
            else:
                with st.spinner("Opening browser..."):
                    try:
                        # Create Selenium service
                        config = SeleniumConfig(headless=False)
                        service = SeleniumService(config)
                        service.start_driver()

                        # Save to session state
                        st.session_state.selenium_service = service

                        # Navigate to login page
                        service.navigate_to(login_url)

                        st.success(
                            """
                            ✅ **Browser opened successfully!**

                            **Next steps:**
                            1. Log in to the site in the browser window
                            2. Complete any 2FA/verification
                            3. Navigate to your target page
                            4. Click "Save Session" below
                            """
                        )

                    except Exception as e:
                        st.error(f"❌ Error opening browser: {e}")

        if st.session_state.selenium_service:
            if st.button("💾 Save Session & Cookies", type="secondary", use_container_width=True):
                service = st.session_state.selenium_service
                cookie_file = Path(f"./cookies/{cookie_name}.json")

                try:
                    service.save_cookies(cookie_file)
                    st.session_state.cookies_saved = True
                    st.session_state.cookie_file = cookie_file

                    st.markdown(
                        f"""
                        <div class="success-box">
                        ✅ <strong>Session saved successfully!</strong><br>
                        📁 Location: <code>{cookie_file}</code><br>
                        🔄 You can now use this session for automated crawling.
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    # Close browser
                    service.stop_driver()
                    st.session_state.selenium_service = None

                except Exception as e:
                    st.error(f"❌ Error saving cookies: {e}")

    with tab2:
        st.markdown("### Load Existing Session")

        cookie_dir = Path("./cookies")
        cookie_dir.mkdir(exist_ok=True)

        cookie_files = list(cookie_dir.glob("*.json"))

        if cookie_files:
            selected_file = st.selectbox(
                "Select a saved session",
                options=cookie_files,
                format_func=lambda x: x.name,
            )

            if st.button("📂 Load This Session", use_container_width=True):
                st.session_state.cookie_file = selected_file
                st.session_state.authenticated = True

                # Show preview
                with open(selected_file, "r") as f:
                    cookies = json.load(f)

                st.success(f"✅ Loaded session: {selected_file.name}")
                st.info(f"📊 Contains {len(cookies)} cookies")

                with st.expander("View Cookie Details"):
                    st.json(cookies)
        else:
            st.info("ℹ️ No saved sessions found. Create one in the 'New Login' tab.")

    with tab3:
        st.markdown(
            """
            ### 📖 Authentication Guide

            #### Why Use Authentication?
            Many sites detect and block automated browsers. Authentication helps by:
            - Using real browser sessions
            - Preserving login state
            - Bypassing "insecure browser" warnings

            #### How It Works:
            1. **Manual Login**: Open a real browser, log in normally
            2. **Save Cookies**: WebClone extracts and saves your session
            3. **Reuse**: Future crawls use these cookies automatically

            #### Security Notes:
            - Cookies are stored locally in `./cookies/` directory
            - Never share cookie files (they contain auth tokens)
            - Sessions expire based on site's policy
            - Re-authenticate when sessions expire

            #### Supported Sites:
            - ✅ Google (Gmail, Drive, etc.)
            - ✅ Facebook
            - ✅ LinkedIn
            - ✅ Twitter/X
            - ✅ GitHub (private repos)
            - ✅ Any site with login requirements

            #### Troubleshooting:
            - **Browser won't open**: Check Chrome/Chromium installation
            - **Cookies not working**: Session may have expired, re-authenticate
            - **Still blocked**: Site may require 2FA or have stricter detection
            """
        )


def page_crawl() -> None:
    """Main crawling interface."""
    show_header()

    st.markdown("## 🌐 Configure & Start Crawl")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### 🎯 Target Configuration")

        target_url = st.text_input(
            "Website URL",
            value="https://example.com",
            help="The starting URL to crawl",
        )

        output_dir = st.text_input(
            "Output Directory",
            value="./website_mirror",
            help="Where to save downloaded content",
        )

        # Advanced settings in expander
        with st.expander("⚙️ Advanced Settings"):
            col_a, col_b = st.columns(2)

            with col_a:
                recursive = st.checkbox("Recursive Crawl", value=True, help="Follow links to other pages")
                max_depth = st.number_input(
                    "Max Depth",
                    min_value=0,
                    value=0,
                    help="Maximum crawl depth (0 = unlimited)",
                )
                max_pages = st.number_input(
                    "Max Pages",
                    min_value=0,
                    value=0,
                    help="Maximum pages to crawl (0 = unlimited)",
                )

            with col_b:
                workers = st.slider("Concurrent Workers", min_value=1, max_value=50, value=5)
                delay_ms = st.slider("Delay (ms)", min_value=0, max_value=5000, value=100)
                same_domain = st.checkbox(
                    "Same Domain Only",
                    value=True,
                    help="Only crawl URLs on the same domain",
                )

            include_assets = st.checkbox("Include Assets (CSS, JS, images)", value=True)
            save_pdf = st.checkbox("Generate PDF Snapshots", value=True)

    with col2:
        st.markdown("### 🔐 Authentication")

        if st.session_state.cookie_file:
            st.success(f"✅ Using session: {st.session_state.cookie_file.name}")
        else:
            st.info("ℹ️ No authentication loaded")
            if st.button("Go to Auth →"):
                st.switch_page("pages/1_🔐_Authentication.py")

        st.markdown("### 📊 Quick Stats")
        st.metric("Workers", workers)
        st.metric("Delay (ms)", delay_ms)

    st.markdown("---")

    # Start button
    col_start, col_stop = st.columns([1, 1])

    with col_start:
        if st.button("▶️ Start Crawl", type="primary", use_container_width=True):
            if not target_url.startswith(("http://", "https://")):
                st.error("❌ Invalid URL. Must start with http:// or https://")
            else:
                # Create configuration
                try:
                    config = CrawlConfig(
                        start_url=target_url,  # type: ignore
                        output_dir=Path(output_dir),
                        recursive=recursive,
                        max_depth=max_depth,
                        max_pages=max_pages,
                        workers=workers,
                        delay_ms=delay_ms,
                        include_assets=include_assets,
                        save_pdf=save_pdf,
                        same_domain_only=same_domain,
                    )

                    # Run crawler
                    with st.spinner("🚀 Crawling in progress..."):
                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        async def run_crawl():
                            async with AsyncCrawler(config) as crawler:
                                result = await crawler.crawl()
                                return result

                        result = asyncio.run(run_crawl())

                        # Save results
                        st.session_state.crawl_results.append(result)

                        st.success(
                            f"""
                            ✅ **Crawl Complete!**

                            - **Pages**: {result.pages_crawled}
                            - **Assets**: {result.assets_downloaded}
                            - **Size**: {result.total_bytes / 1024 / 1024:.2f} MB
                            - **Duration**: {result.duration_seconds:.2f}s
                            """
                        )

                except Exception as e:
                    st.error(f"❌ Error: {e}")

    with col_stop:
        if st.button("⏹️ Stop Crawl", type="secondary", use_container_width=True):
            st.warning("⚠️ Stop functionality requires background task management")


def page_results() -> None:
    """Results and analytics page."""
    show_header()

    st.markdown("## 📊 Crawl Results & Analytics")

    if not st.session_state.crawl_results:
        st.info("ℹ️ No crawl results yet. Start a crawl to see statistics here.")
        return

    # Show latest result
    latest = st.session_state.crawl_results[-1]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Pages Crawled", latest.pages_crawled)

    with col2:
        st.metric("Assets Downloaded", latest.assets_downloaded)

    with col3:
        st.metric("Total Size", f"{latest.total_bytes / 1024 / 1024:.2f} MB")

    with col4:
        st.metric("Duration", f"{latest.duration_seconds:.2f}s")

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📄 Pages", "📦 Assets", "📈 Analytics"])

    with tab1:
        st.markdown("### Crawled Pages")
        if latest.pages:
            for page in latest.pages[:10]:  # Show first 10
                with st.expander(f"🌐 {page.url}"):
                    st.markdown(f"**Title:** {page.title or 'N/A'}")
                    st.markdown(f"**Status:** {page.status_code}")
                    st.markdown(f"**Depth:** {page.crawl_depth}")
                    st.markdown(f"**Links Found:** {len(page.discovered_links)}")
                    st.markdown(f"**Assets:** {page.assets_count}")

    with tab2:
        st.markdown("### Downloaded Assets")
        if latest.assets:
            # Group by type
            asset_types = {}
            for asset in latest.assets:
                asset_types.setdefault(asset.resource_type.value, []).append(asset)

            for resource_type, assets in asset_types.items():
                st.markdown(f"**{resource_type.upper()}**: {len(assets)} files")

    with tab3:
        st.markdown("### Performance Analytics")

        # Calculate metrics
        avg_speed = latest.total_bytes / latest.duration_seconds if latest.duration_seconds > 0 else 0

        st.metric("Average Speed", f"{avg_speed / 1024 / 1024:.2f} MB/s")
        st.metric("Pages per Second", f"{latest.pages_crawled / latest.duration_seconds:.2f}")

        if latest.errors:
            st.warning(f"⚠️ {len(latest.errors)} errors occurred during crawl")
            with st.expander("View Errors"):
                for error in latest.errors:
                    st.text(error)


def main() -> None:
    """Main application entry point."""
    initialize_session_state()

    # Sidebar navigation
    with st.sidebar:
        st.image("https://via.placeholder.com/150?text=WebClone", width=150)

        selected = option_menu(
            "Navigation",
            ["Home", "Authentication", "Crawl Website", "Results"],
            icons=["house", "key", "download", "bar-chart"],
            menu_icon="cast",
            default_index=0,
        )

        st.markdown("---")
        st.markdown(
            """
            ### 📚 Resources
            - [Documentation](https://ruslanmv.com)
            - [GitHub](https://github.com/ruslanmv/webclone)
            - [Report Issue](https://github.com/ruslanmv/webclone/issues)
            """
        )

        st.markdown(f"**Version:** {__version__}")

    # Route to pages
    if selected == "Home":
        page_home()
    elif selected == "Authentication":
        page_authenticate()
    elif selected == "Crawl Website":
        page_crawl()
    elif selected == "Results":
        page_results()


if __name__ == "__main__":
    main()
