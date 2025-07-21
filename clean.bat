@echo off
echo ========================================
echo 🧹 Pixeltovoxelprojector Cleanup
echo ========================================
echo.

echo ⚠️  WARNUNG: Dieses Script löscht ALLE generierten Dateien!
echo    - Test-Daten
echo    - Proof-Videos und Bilder  
echo    - Reports und Logs
echo    - Build-Artefakte
echo.
set /p confirm="Sind Sie sicher? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo Abgebrochen.
    pause
    exit /b 0
)

echo.
echo 🗑️  Lösche generierte Dateien...

:: Test-Daten löschen
echo Lösche Test-Daten...
if exist "mosquito_tracking\mosquito_test" rmdir /s /q "mosquito_tracking\mosquito_test"
if exist "mosquito_tracking\realistic_mosquito_test" rmdir /s /q "mosquito_tracking\realistic_mosquito_test"
if exist "tests\motionimages" rmdir /s /q "tests\motionimages"
if exist "tests\webcam_motion" rmdir /s /q "tests\webcam_motion"

:: Proof-Verzeichnisse löschen
echo Lösche Proof-Dateien...
for /d %%d in (proof_*) do rmdir /s /q "%%d"
for /d %%d in (mosquito_tracking\proof_*) do rmdir /s /q "%%d"
for /d %%d in (live_mosquito_*) do rmdir /s /q "%%d"

:: Videos löschen
echo Lösche Videos...
del /q *.mp4 2>nul
del /q *.avi 2>nul
del /q mosquito_tracking\*.mp4 2>nul
del /q mosquito_tracking\*.avi 2>nul

:: Reports löschen
echo Lösche Reports...
del /q *_report_*.* 2>nul
del /q mosquito_tracking\*_report_*.* 2>nul
del /q mosquito_tracking\mosquito_test_results_*.html 2>nul

:: Bilder löschen (generierte)
echo Lösche generierte Bilder...
del /q mosquito_tracking\*.png 2>nul
del /q tests\*.png 2>nul

:: Build-Artefakte löschen
echo Lösche Build-Artefakte...
if exist "build" rmdir /s /q "build"
if exist "__pycache__" rmdir /s /q "__pycache__"
if exist "mosquito_tracking\__pycache__" rmdir /s /q "mosquito_tracking\__pycache__"
if exist "tools\__pycache__" rmdir /s /q "tools\__pycache__"
if exist "tests\__pycache__" rmdir /s /q "tests\__pycache__"

:: Temp-Dateien löschen
echo Lösche Temp-Dateien...
del /q *.tmp 2>nul
del /q *.temp 2>nul
del /q *.log 2>nul

:: Kompilierte Module löschen (können regeneriert werden)
echo Lösche kompilierte Module...
del /q core\*.exe 2>nul
del /q core\*.obj 2>nul
del /q core\*.pyd 2>nul
del /q *.bin 2>nul

echo.
echo ✅ Cleanup abgeschlossen!
echo.
echo 🔄 Um alle Dateien wiederherzustellen, führen Sie aus:
echo    install.bat
echo.
pause
