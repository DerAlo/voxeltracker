#!/usr/bin/env python3

import json
import numpy as np
from PIL import Image
import os
import random
import math

def create_mosquito_test_data():
    """
    Erstellt realistische Testdaten für Mücken-Tracking
    - Sehr kleine Objekte (1-3 Pixel)
    - Unregelmäßige, zufällige Bewegungsmuster
    - Verschiedene Geschwindigkeiten
    - Realistische Größen und Bewegungen
    """
    
    # Erstelle Testverzeichnis
    os.makedirs("mosquito_test", exist_ok=True)
    
    # Parameter für realistische Mückensimulation
    num_frames = 30  # 30 Frames für ein kurzes Video
    img_width, img_height = 640, 480  # Normale Webcam-Auflösung
    num_mosquitos = 3  # Mehrere Mücken gleichzeitig
    
    frames = []
    mosquito_positions = []
    
    # Initialisiere Mückenpositionen
    for i in range(num_mosquitos):
        mosquito_positions.append({
            'x': random.randint(50, img_width - 50),
            'y': random.randint(50, img_height - 50),
            'vx': random.uniform(-3, 3),  # Geschwindigkeit in x-Richtung
            'vy': random.uniform(-3, 3),  # Geschwindigkeit in y-Richtung
            'size': random.randint(1, 3),  # Mückengröße (sehr klein)
            'brightness': random.randint(100, 200)  # Helligkeit
        })
    
    for frame_idx in range(num_frames):
        # Erstelle graues Hintergrundbild (simuliert normales Webcam-Bild)
        img = np.random.randint(80, 120, (img_height, img_width, 3), dtype=np.uint8)
        
        # Füge etwas Textur/Rauschen hinzu (wie bei echter Webcam)
        noise = np.random.randint(-20, 20, (img_height, img_width, 3))
        img = np.clip(img.astype(int) + noise, 0, 255).astype(np.uint8)
        
        # Bewege und zeichne jede Mücke
        for mosquito in mosquito_positions:
            # Unregelmäßige Bewegung (Mücken fliegen nicht geradeaus)
            if random.random() < 0.3:  # 30% Chance für Richtungsänderung
                mosquito['vx'] += random.uniform(-1, 1)
                mosquito['vy'] += random.uniform(-1, 1)
                
            # Begrenze Geschwindigkeit
            mosquito['vx'] = max(-5, min(5, mosquito['vx']))
            mosquito['vy'] = max(-5, min(5, mosquito['vy']))
            
            # Update Position
            mosquito['x'] += mosquito['vx']
            mosquito['y'] += mosquito['vy']
            
            # Rand-Kollision (Mücken prallen ab)
            if mosquito['x'] <= 0 or mosquito['x'] >= img_width:
                mosquito['vx'] *= -1
                mosquito['x'] = max(0, min(img_width-1, mosquito['x']))
            if mosquito['y'] <= 0 or mosquito['y'] >= img_height:
                mosquito['vy'] *= -1
                mosquito['y'] = max(0, min(img_height-1, mosquito['y']))
            
            # Zeichne Mücke (sehr kleiner dunkler Punkt)
            x, y = int(mosquito['x']), int(mosquito['y'])
            size = mosquito['size']
            brightness = mosquito['brightness']
            
            # Zeichne Mücke als kleinen dunklen Punkt
            for dx in range(-size, size+1):
                for dy in range(-size, size+1):
                    if 0 <= x+dx < img_width and 0 <= y+dy < img_height:
                        # Machen die Mücke dunkler als der Hintergrund
                        img[y+dy, x+dx] = [brightness//3, brightness//3, brightness//3]
        
        # Speichere Bild
        image_path = f"mosquito_test/mosquito_frame_{frame_idx:03d}.png"
        Image.fromarray(img).save(image_path)
        print(f"Erstellt {image_path} mit {num_mosquitos} Mücken")
        
        # Erstelle Frame-Metadaten
        frame_info = {
            "filename": f"mosquito_frame_{frame_idx:03d}.png",
            "timestamp": frame_idx * 0.033,  # ~30 FPS (0.033 Sekunden pro Frame)
            "camera_index": 0,
            "camera_x": 0.0,
            "camera_y": 0.0,
            "camera_z": 2.0,  # Näher zur Szene für bessere Auflösung
            "rotation_x": 0.0,
            "rotation_y": 0.0,
            "rotation_z": 0.0,
            "mosquito_count": num_mosquitos,
            "detection_profile": "Mosquito 🦟"
        }
        frames.append(frame_info)
    
    # Speichere Metadaten
    with open("mosquito_test/metadata.json", "w") as f:
        json.dump(frames, f, indent=2)
    
    print(f"\n✅ Mücken-Testdaten erfolgreich erstellt!")
    print(f"📁 Verzeichnis: mosquito_test/")
    print(f"🖼️  {num_frames} Bilder mit {num_mosquitos} simulierten Mücken")
    print(f"📋 metadata.json mit Frame-Informationen")
    print(f"🎯 Optimiert für das 'Mosquito 🦟' Profil")

def create_real_mosquito_simulation():
    """
    Erstellt eine noch realistischere Simulation basierend auf echtem Mückenverhalten
    """
    os.makedirs("realistic_mosquito_test", exist_ok=True)
    
    # Realistische Parameter
    num_frames = 60  # 2 Sekunden bei 30 FPS
    img_width, img_height = 640, 480
    
    frames = []
    
    # Simuliere verschiedene Mückenarten und -verhalten
    mosquito_scenarios = [
        {"name": "hovering", "description": "Mücke schwebt an einer Stelle"},
        {"name": "searching", "description": "Mücke sucht nach Nahrung (zufällige Bewegung)"},
        {"name": "escaping", "description": "Mücke flieht schnell"}
    ]
    
    for scenario_idx, scenario in enumerate(mosquito_scenarios):
        scenario_frames = 20  # 20 Frames pro Szenario
        
        # Mückenposition für dieses Szenario
        mosquito = {
            'x': random.randint(100, img_width - 100),
            'y': random.randint(100, img_height - 100),
            'vx': 0,
            'vy': 0
        }
        
        for frame_idx in range(scenario_frames):
            # Hintergrundbild
            img = np.random.randint(90, 130, (img_height, img_width, 3), dtype=np.uint8)
            
            # Bewegungsmuster je nach Szenario
            if scenario["name"] == "hovering":
                # Kleine zufällige Bewegungen um eine Position
                mosquito['vx'] = random.uniform(-0.5, 0.5)
                mosquito['vy'] = random.uniform(-0.5, 0.5)
            elif scenario["name"] == "searching":
                # Zufällige Suchbewegungen
                if random.random() < 0.4:
                    mosquito['vx'] = random.uniform(-2, 2)
                    mosquito['vy'] = random.uniform(-2, 2)
            elif scenario["name"] == "escaping":
                # Schnelle, gerichtete Flucht
                mosquito['vx'] = random.uniform(-4, 4)
                mosquito['vy'] = random.uniform(-4, 4)
            
            # Position aktualisieren
            mosquito['x'] += mosquito['vx']
            mosquito['y'] += mosquito['vy']
            
            # Grenzen einhalten
            mosquito['x'] = max(10, min(img_width-10, mosquito['x']))
            mosquito['y'] = max(10, min(img_height-10, mosquito['y']))
            
            # Zeichne Mücke (1-2 Pixel groß)
            x, y = int(mosquito['x']), int(mosquito['y'])
            img[y-1:y+2, x-1:x+2] = [60, 60, 60]  # Dunkler Punkt
            
            # Speichere Bild
            frame_number = scenario_idx * scenario_frames + frame_idx
            image_path = f"realistic_mosquito_test/realistic_mosquito_{frame_number:03d}.png"
            Image.fromarray(img).save(image_path)
            
            # Metadaten
            frame_info = {
                "filename": f"realistic_mosquito_{frame_number:03d}.png",
                "timestamp": frame_number * 0.033,
                "camera_index": 0,
                "camera_x": 0.0,
                "camera_y": 0.0,
                "camera_z": 1.5,
                "rotation_x": 0.0,
                "rotation_y": 0.0,
                "rotation_z": 0.0,
                "scenario": scenario["name"],
                "description": scenario["description"]
            }
            frames.append(frame_info)
    
    # Speichere Metadaten
    with open("realistic_mosquito_test/metadata.json", "w") as f:
        json.dump(frames, f, indent=2)
    
    print(f"\n✅ Realistische Mücken-Testdaten erstellt!")
    print(f"📁 Verzeichnis: realistic_mosquito_test/")
    print(f"🎬 3 verschiedene Verhaltensszenarien simuliert")

if __name__ == "__main__":
    create_mosquito_test_data()
    create_real_mosquito_simulation()
    print("\n🔬 Alle Mücken-Testdaten erstellt. Bereit für Tests!")
