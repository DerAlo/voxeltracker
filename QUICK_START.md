# 🚀 Quick Setup Guide

## ⚡ 30-Sekunden Start

```bash
# 1. Ins Mosquito-Tracking wechseln
cd mosquito_tracking

# 2. Live-Tracking starten
python live_mosquito_tracker.py

# 3. Mücke vor Kamera halten
# 4. Profit! 🦟✅
```

## 📋 Requirements Check

```bash
# Python Dependencies prüfen
python -c "import cv2, numpy, json, os, time, datetime, threading, queue; print('✅ Alle Module verfügbar!')"

# Webcam testen
python -c "import cv2; cap = cv2.VideoCapture(0); print('✅ Webcam funktioniert!' if cap.isOpened() else '❌ Webcam Problem'); cap.release()"
```

## 🎯 Schnelltest

```bash
# Kompletter Test-Durchlauf (5 Minuten)
cd mosquito_tracking
python create_mosquito_test_data.py    # Erstellt Test-Daten
python mosquito_test_validator.py      # Validiert System  
python create_final_report.py          # Erstellt Berichte

# Live-Test mit Webcam
python live_mosquito_tracker.py        # Live-Tracking starten
```

## 💡 Troubleshooting

**Problem:** Webcam nicht erkannt
```bash
# Lösung: Anderen USB-Port probieren oder Index ändern
# In live_mosquito_tracker.py Zeile: camera_index = 1  # statt 0
```

**Problem:** Zu viele Falsch-Positive
```bash
# Lösung: Sensitivität reduzieren
# Drücken Sie '-' Taste während Live-Tracking
```

**Problem:** Mücken nicht erkannt  
```bash
# Lösung: Bessere Beleuchtung + höhere Sensitivität
# Drücken Sie '+' Taste während Live-Tracking
```

## ✅ System bereit!

Ihr **Pixeltovoxelprojector** ist jetzt sauber organisiert und produktionsreif! 🎉
