#!/usr/bin/env python3
"""
WebMirror GUI Launcher

Simple launcher script for the WebMirror enterprise desktop GUI.
Double-click this file or run from command line.

Author: Ruslan Magana
Website: ruslanmv.com
"""

import sys
from pathlib import Path


def main() -> None:
    """Launch the WebMirror GUI."""
    print("=" * 70)
    print("🌐 WebMirror - Professional Website Cloning Engine")
    print("=" * 70)
    print()
    print("🚀 Starting Enterprise Desktop GUI...")
    print("=" * 70)
    print()

    # Add src directory to path
    src_path = Path(__file__).parent / "src"
    if not src_path.exists():
        print(f"❌ Error: Could not find src directory at {src_path}")
        print("Make sure you're running this from the WebMirror root directory.")
        sys.exit(1)

    sys.path.insert(0, str(src_path))

    try:
        # Import and launch the GUI
        from webmirror.gui.tkinter_app import WebMirrorGUI

        app = WebMirrorGUI()
        app.run()

    except ImportError as e:
        print("❌ Error: Could not import GUI module!")
        print()
        print(f"Details: {e}")
        print()
        print("Please install GUI dependencies:")
        print("  make install-gui")
        print()
        print("Or manually:")
        print("  pip install ttkbootstrap")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
