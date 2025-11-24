#!/usr/bin/env python3
"""
WebMirror GUI Launcher

Simple launcher script for the WebMirror web interface.
Double-click this file or run from command line.

Author: Ruslan Magana
Website: ruslanmv.com
"""

import subprocess
import sys
from pathlib import Path


def main() -> None:
    """Launch the WebMirror GUI."""
    print("=" * 70)
    print("🌐 WebMirror - Professional Website Cloning Engine")
    print("=" * 70)
    print()
    print("🚀 Starting Web GUI...")
    print("📍 Opening in your browser...")
    print()
    print("💡 The interface will open automatically at: http://localhost:8501")
    print()
    print("✋ Press Ctrl+C to stop the server")
    print("=" * 70)
    print()

    # Get the path to the streamlit app
    app_path = Path(__file__).parent / "src" / "webmirror" / "gui" / "streamlit_app.py"

    if not app_path.exists():
        print(f"❌ Error: Could not find GUI app at {app_path}")
        print("Make sure you're running this from the WebMirror root directory.")
        sys.exit(1)

    try:
        # Launch streamlit
        subprocess.run(
            ["streamlit", "run", str(app_path)],
            check=True,
        )
    except KeyboardInterrupt:
        print("\n")
        print("=" * 70)
        print("✅ WebMirror GUI stopped")
        print("=" * 70)
    except FileNotFoundError:
        print("❌ Error: Streamlit not found!")
        print()
        print("Please install GUI dependencies:")
        print("  make install-gui")
        print()
        print("Or manually:")
        print("  pip install streamlit streamlit-option-menu")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
