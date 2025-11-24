@echo off
REM WebMirror GUI Launcher for Windows
REM Double-click this file to start the GUI

echo ======================================================================
echo    WebMirror - Professional Website Cloning Engine
echo ======================================================================
echo.
echo Starting Web GUI...
echo Opening in your browser...
echo.
echo The interface will open at: http://localhost:8501
echo.
echo Press Ctrl+C to stop the server
echo ======================================================================
echo.

streamlit run src\webmirror\gui\streamlit_app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ======================================================================
    echo Error: Could not start GUI!
    echo.
    echo Please install GUI dependencies:
    echo   make install-gui
    echo.
    echo Or manually:
    echo   pip install streamlit streamlit-option-menu
    echo ======================================================================
    pause
)
