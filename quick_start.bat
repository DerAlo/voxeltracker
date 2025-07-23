@echo off
echo ========================================
echo 🚀 VoxelTracker Quick Start
echo ========================================
echo.

echo 📋 Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python nicht gefunden! Bitte installieren Sie Python 3.9+
    echo    Download: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo ✅ Python gefunden

echo.
echo 📦 Installing required dependencies...
pip install opencv-python numpy pillow pyvista yt-dlp >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Installation fehlgeschlagen
    echo Versuche detaillierte Installation...
    pip install opencv-python numpy pillow pyvista yt-dlp
    if %errorlevel% neq 0 (
        echo ❌ Kritischer Fehler bei der Installation
        pause
        exit /b 1
    )
)
echo ✅ Dependencies installiert

echo.
echo 🎯 Starting Master Motion Tracker...
echo ========================================
echo.
python master_motion_tracker.py

echo.
echo ========================================
echo Program beendet. Drücken Sie eine Taste...
pause >nul
