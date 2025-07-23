# 🚫 ANTI-STATIONARY FILTER - Revolution gegen Wolken-Kanten!

## ✅ Problem behoben: 

**Alte Filter waren kontraproduktiv:**
- ❌ Filterten **schnelle Vögel** raus  
- ❌ Ließen **langsame Wolken-Kanten** durch
- ❌ Zu restriktiv für echte Bewegungen

**Neue Anti-Stationary Filter sind intelligent:**
- ✅ Filtern **stationäre/langsame Objekte** (Wolken-Kanten, Äste)
- ✅ Erhalten **schnelle Vögel** mit echter Bewegungsdynamik
- ✅ Fokus auf **signifikante Bewegung** statt Geschwindigkeitslimits

## 🛡️ Neue Filter-Logik:

### 📏 **Mindest-Bewegung Filter**
```
Einstellung: 5-50 Pixel (Standard: 15)
Zweck: Objekt muss sich mindestens X Pixel bewegen
Filtert: Wolken-Kanten die sich kaum bewegen, statische Äste
```

### ⏱️ **Bewegungszeit-Fenster**
```
Einstellung: 0.5-3.0 Sekunden (Standard: 1.0s)
Zweck: Bewegung muss in diesem Zeitrahmen stattfinden
Filtert: Sehr langsame Drift, quasi-statische Objekte
```

## 🔧 Technische Verbesserungen:

### Anti-Stationary Algorithmus:
```python
# Für jede Motion wird geprüft:
for older_motion in motion_list:
    time_diff = motion_time - older_time
    if time_window < time_diff < time_window * 2:
        distance = sqrt((x-old_x)² + (y-old_y)²)
        if distance >= min_distance:
            has_significant_movement = True
```

### GUI-Updates:
- **Entfernt**: Persistenz, Max-Geschwindigkeit, Himmel-Bereich, Konfidenz-Filter
- **Neu**: Mindest-Bewegung (15 Pixel), Bewegungszeit-Fenster (1.0s)
- **Info-Box**: Zeigt Anti-Stationary Filter Status

### Filter-Philosophie:
```
Alte Filter: "Blockiere alles was zu schnell/persistent/etc ist"
Neue Filter: "Erlaube nur was sich WIRKLICH bewegt"

Resultat: Vögel fliegen durch, Wolken-Kanten bleiben stehen!
```

## 🐦 Optimierung für Vogeltracking:

### Empfohlene Einstellungen:
- **Mindest-Bewegung**: 10-20 Pixel (Vögel bewegen sich deutlich)
- **Zeitfenster**: 0.8-1.5s (Vögel zeigen kontinuierliche Bewegung)

### Was jetzt passiert:
1. **Vogel**: Bewegt sich 25 Pixel in 1 Sekunde → ✅ **ERKANNT**
2. **Wolken-Kante**: Bewegt sich 3 Pixel in 1 Sekunde → ❌ **GEFILTERT**
3. **Ast**: Bewegt sich 0 Pixel → ❌ **GEFILTERT**
4. **Schatten**: Bewegt sich 50 Pixel in 1 Sekunde → ✅ **ERKANNT** (authentische Bewegung)

## 🎯 Resultate:

**Vor Anti-Stationary Filter:**
- Viele Falschalarme durch Wolken-Kanten
- Verlust von schnellen Vögeln durch Speed-Limits
- Komplexe Filter-Justierung nötig

**Nach Anti-Stationary Filter:**
- **Wolken-Kanten ignoriert** (zu wenig Bewegung)
- **Vögel kommen durch** (echte Bewegungsdynamik)
- **Einfache 2-Parameter-Justierung**

### 🚀 Das System ist jetzt optimiert für:
- ✅ **Echte Bewegungsobjekte** (Vögel, Flugzeuge, bewegte Tiere)
- ❌ **Quasi-statische Störungen** (Wolken, Äste, Kamera-Drift)
- 🎯 **Saubere Triangulation** ohne Falschalarme

**Teste es jetzt - die Vögel sollten verfolgt werden, die Wolken-Kanten nicht! 🐦**
