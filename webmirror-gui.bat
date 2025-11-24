@echo off
REM WebMirror Enterprise GUI Launcher for Windows
REM Double-click this file to start the desktop GUI

echo ======================================================================
echo    WebMirror - Professional Website Cloning Engine
echo ======================================================================
echo.
echo Starting Enterprise Desktop GUI...
echo ======================================================================
echo.

python webmirror-gui.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ======================================================================
    echo Error: Could not start GUI!
    echo.
    echo Please install GUI dependencies:
    echo   make install-gui
    echo.
    echo Or manually:
    echo   pip install ttkbootstrap
    echo ======================================================================
    pause
)
