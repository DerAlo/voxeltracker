# 🚨 Nach dem Klonen ausführen!

## ⚡ Sofortiger Start

```bash
# 1. Repository klonen
git clone <your-repo-url>
cd Pixeltovoxelprojector

# 2. Setup ausführen (erstellt alle fehlenden Dateien)
install.bat

# 3. Mosquito-Tracking testen
cd mosquito_tracking
python live_mosquito_tracker.py
```

## 📁 Was wird erstellt?

Das `install.bat` Script erstellt automatisch:
- ✅ Test-Daten (mosquito_test/, realistic_mosquito_test/)
- ✅ Kompilierte C++ Module
- ✅ Beispiel-Videos und Berichte
- ✅ Proof-of-Concept Dateien

## 🧹 Cleanup

```bash
# Alle generierten Dateien löschen (für sauberes Git)
clean.bat

# Alles wiederherstellen
install.bat
```

## 📋 Requirements

- **Python 3.9+**
- **Windows** (Batch-Scripts)
- **Webcam** (für Live-Tests)

Das wars! 🎉
