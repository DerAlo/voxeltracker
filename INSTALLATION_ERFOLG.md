🎯 VoxelTracker - Schnellstart
============================

## Einfache Installation und Start:

1. **Automatischer Start:**
   - Doppelklick auf `quick_start.bat`
   - Das Script installiert alle benötigten Pakete und startet die Anwendung

2. **Manuelle Installation (falls nötig):**
   - Führe `install.bat` aus für vollständige Installation
   - Dann: `python master_motion_tracker.py`

## Was läuft jetzt:

✅ **Master Motion Tracker** - Das Hauptprogramm mit GUI
- Verschiedene Tracking-Modi (Mücken, Vögel, Flugzeuge)
- Unterstützung für Webcams und YouTube Live-Streams
- 3D-Visualisierung mit PyVista

## Installierte Dependencies:

✅ **OpenCV** - Computer Vision
✅ **NumPy** - Numerische Berechnungen  
✅ **Pillow** - Bildverarbeitung
✅ **PyVista** - 3D-Visualisierung
✅ **yt-dlp** - YouTube Stream Support

## Verwendung:

1. **Starte die Anwendung:** `quick_start.bat` oder `python master_motion_tracker.py`
2. **Wähle ein Profil:** Mücken 🦟, Vögel 🐦, Flugzeuge ✈️
3. **Wähle eine Quelle:** Webcam oder Stream
4. **Starte das Tracking!**

## Bemerkungen:

- C++ Module sind optional und wurden übersprungen (nicht benötigt für Grundfunktionen)
- Alle Test-Daten sind optional
- Das System läuft vollständig mit Python

## Bei Problemen:

1. Prüfe Python-Installation: `python --version`
2. Reinstalliere Pakete: `pip install opencv-python numpy pillow pyvista yt-dlp`
3. Starte neu: `python master_motion_tracker.py`
