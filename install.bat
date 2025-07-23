@echo off
echo ========================================
echo 🚀 Pixeltovoxelprojector Setup
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
echo 📦 Installing Python dependencies...
echo Installing from requirements.txt...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ❌ Fehler beim Installieren der Dependencies
    echo Versuche manuelle Installation...
    pip install opencv-python numpy pillow pyvista
    if %errorlevel% neq 0 (
        echo ❌ Manuelle Installation fehlgeschlagen
        pause
        exit /b 1
    )
)

echo.
echo 📦 Installing additional dependencies...
pip install yt-dlp
if %errorlevel% neq 0 (
    echo ⚠️  yt-dlp installation failed - YouTube features may not work
) else (
    echo ✅ yt-dlp installiert
)

echo ✅ Dependencies installiert

echo.
echo 🔨 Checking for C++ modules...
cd core
if exist setup.py (
    echo ⚠️  C++ modules detected but skipping compilation (optional)
    echo    Install pybind11 and Microsoft Visual Studio Build Tools if needed
) else (
    echo ⚠️  setup.py nicht gefunden, überspringe C++ Kompilierung
)
cd ..

echo.
echo 🧪 Setting up test environment (optional)...
if exist mosquito_tracking\create_mosquito_test_data.py (
    cd mosquito_tracking
    python create_mosquito_test_data.py >nul 2>&1
    echo ✅ Mosquito test data erstellt
    cd ..
) else (
    echo ⚠️  Mosquito test data creation skipped
)

if exist tests\create_test_data.py (
    cd tests
    python create_test_data.py >nul 2>&1
    echo ✅ General test data erstellt
    cd ..
) else (
    echo ⚠️  General test data creation skipped
)

echo.
echo ========================================
echo 🎉 SETUP ABGESCHLOSSEN!
echo ========================================
echo.
echo 🎯 Starting Master Motion Tracker...
echo.
echo 📚 Dokumentation:
echo    README.md - Hauptübersicht
echo    QUICK_START.md - Schnellstart
echo    docs/FOLDER_STRUCTURE.md - Ordnerstruktur
echo.
echo Starting main application in 3 seconds...
timeout /t 3 >nul
python master_motion_tracker.py
