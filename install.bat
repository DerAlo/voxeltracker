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
echo ✅ Dependencies installiert

echo.
echo 🔨 Compiling C++ modules...
cd core
if exist setup.py (
    python setup.py build_ext --inplace
    echo ✅ C++ Module kompiliert
) else (
    echo ⚠️  setup.py nicht gefunden, überspringe C++ Kompilierung
)
cd ..

echo.
echo 🧪 Creating test data...
cd mosquito_tracking
python create_mosquito_test_data.py
echo ✅ Mosquito test data erstellt
cd ..

echo.
echo 🧪 Creating general test data...
cd tests
python create_test_data.py
echo ✅ General test data erstellt
cd ..

echo.
echo 🎯 Running system validation...
cd mosquito_tracking
python mosquito_test_validator.py
echo ✅ System validiert
cd ..

echo.
echo 📊 Generating reports...
cd mosquito_tracking
python create_final_report.py
echo ✅ Reports erstellt
cd ..

echo.
echo ========================================
echo 🎉 SETUP ABGESCHLOSSEN!
echo ========================================
echo.
echo 🦟 Für Mosquito-Tracking:
echo    cd mosquito_tracking
echo    python live_mosquito_tracker.py
echo.
echo 🔧 Für andere Tools:
echo    cd tools
echo    python launcher.py
echo.
echo 📚 Dokumentation:
echo    README.md - Hauptübersicht
echo    QUICK_START.md - Schnellstart
echo    docs/FOLDER_STRUCTURE.md - Ordnerstruktur
echo.
pause
