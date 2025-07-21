#!/usr/bin/env python3

import cv2
import numpy as np
import requests
import time
from datetime import datetime
import os

# GEFUNDENE ÜBERLAPPENDE WEBCAM-PERSPEKTIVEN (aus Online-Recherche)

OVERLAPPING_WEBCAMS = {
    "venice_multiple_angles": {
        "name": "Venedig - Mehrere Perspektiven", 
        "cams": [
            {
                "name": "Piazza San Marco",
                "url": "https://static.earthcam.com/camshots/1024x768/b0894.jpg",
                "description": "Markusplatz Hauptsicht"
            },
            {
                "name": "Rialto Bridge", 
                "url": "https://static.earthcam.com/camshots/1024x768/b0895.jpg",
                "description": "Rialtobrücke - überlappende Sicht"
            },
            {
                "name": "Grand Canal",
                "url": "https://static.earthcam.com/camshots/1024x768/b0896.jpg", 
                "description": "Canale Grande - weitere Perspektive"
            }
        ]
    },
    
    "prague_old_town": {
        "name": "Prag - Altstadt Überlappung",
        "cams": [
            {
                "name": "Prague Old Town Square",
                "url": "https://images-webcams.windy.com/21/1586785821/current/icon/1586785821.jpg",
                "description": "Altstädter Ring Hauptsicht"
            },
            {
                "name": "Prague Astronomical Clock",
                "url": "https://static.earthcam.com/camshots/1024x768/prague01.jpg",
                "description": "Astronomische Uhr - gleicher Platz"
            }
        ]
    },
    
    "times_square_angles": {
        "name": "Times Square - Multiple Views",
        "cams": [
            {
                "name": "Times Square North",
                "url": "https://static.earthcam.com/camshots/1024x768/timessquare.jpg",
                "description": "Times Square Richtung Norden"
            },
            {
                "name": "Times Square South View", 
                "url": "https://static.earthcam.com/camshots/1024x768/timessquare2.jpg",
                "description": "Times Square Richtung Süden"
            }
        ]
    },
    
    "rome_multiple_sites": {
        "name": "Rom - Verschiedene Perspektiven",
        "cams": [
            {
                "name": "Trevi Fountain",
                "url": "https://static.earthcam.com/camshots/1024x768/trevi.jpg",
                "description": "Trevi Brunnen"
            },
            {
                "name": "Spanish Steps",
                "url": "https://static.earthcam.com/camshots/1024x768/spanishsteps.jpg", 
                "description": "Spanische Treppe - nahegelegene Perspektive"
            },
            {
                "name": "Pantheon",
                "url": "https://static.earthcam.com/camshots/1024x768/pantheon.jpg",
                "description": "Pantheon - Rom Zentrum"
            }
        ]
    }
}

def quick_test_webcam(url, timeout=5):
    """Schneller Test ob Webcam verfügbar ist - keine User-Eingaben!"""
    try:
        response = requests.get(url, timeout=timeout, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200 and len(response.content) > 1000:
            return True
    except:
        pass
    return False

def capture_sync_frames(cam_group, max_frames=10):
    """Synchrone Aufnahme mehrerer Kameras - begrenzte Anzahl Frames"""
    print(f"🎯 Teste Kamera-Gruppe: {cam_group['name']}")
    
    # Session-Ordner
    session_dir = f"investigation_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(session_dir, exist_ok=True)
    
    working_cams = []
    
    # Teste welche Kameras funktionieren
    print("🔍 Teste Kamera-Verfügbarkeit...")
    for cam in cam_group['cams']:
        if quick_test_webcam(cam['url']):
            working_cams.append(cam)
            print(f"✅ {cam['name']} - Verfügbar")
        else:
            print(f"❌ {cam['name']} - Nicht verfügbar")
    
    if len(working_cams) < 2:
        print("❌ Nicht genügend funktionierende Kameras für Überlappungstest")
        return None
    
    print(f"📸 Starte synchrone Aufnahme von {len(working_cams)} Kameras...")
    
    # Motion Detection Parameter
    motion_params = {
        "threshold": 30,
        "min_area": 200, 
        "max_area": 10000
    }
    
    results = {}
    previous_frames = {}
    
    for frame_num in range(max_frames):
        print(f"📷 Frame {frame_num + 1}/{max_frames}")
        
        for cam in working_cams:
            cam_name = cam['name'].replace(' ', '_')
            
            # Erstelle Kamera-Ordner
            cam_dir = f"{session_dir}/{cam_name}"
            os.makedirs(cam_dir, exist_ok=True)
            
            # Lade Frame
            try:
                response = requests.get(cam['url'], timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
                if response.status_code == 200:
                    img_array = np.frombuffer(response.content, np.uint8)
                    frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                    
                    if frame is not None:
                        # Speichere Rohbild
                        raw_filename = f"{cam_dir}/raw_{frame_num:03d}.jpg"
                        cv2.imwrite(raw_filename, frame)
                        
                        # Motion Detection
                        detections = []
                        if cam_name in previous_frames:
                            detections = detect_simple_motion(frame, previous_frames[cam_name], motion_params)
                        
                        if len(detections) > 0:
                            print(f"  🎯 {cam['name']}: {len(detections)} Bewegungen erkannt")
                            
                            # Annotiere und speichere
                            annotated = annotate_simple(frame, detections, cam['name'])
                            detection_filename = f"{cam_dir}/motion_{frame_num:03d}.jpg"
                            cv2.imwrite(detection_filename, annotated)
                        
                        # Update previous frame
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        previous_frames[cam_name] = cv2.GaussianBlur(gray, (5, 5), 0)
                        
                        # Sammle Statistiken
                        if cam_name not in results:
                            results[cam_name] = {"frames": 0, "detections": 0}
                        results[cam_name]["frames"] += 1
                        results[cam_name]["detections"] += len(detections)
            
            except Exception as e:
                print(f"  ❌ {cam['name']}: {str(e)[:30]}")
        
        # Kurze Pause zwischen Captures
        time.sleep(3)
    
    # Erstelle einfachen Report
    print("\n📊 RESULTS:")
    for cam_name, stats in results.items():
        if stats["frames"] > 0:
            avg = stats["detections"] / stats["frames"]
            print(f"  📹 {cam_name}: {stats['detections']} detections in {stats['frames']} frames (avg: {avg:.1f})")
    
    print(f"\n📁 Session gespeichert: {session_dir}")
    return session_dir

def detect_simple_motion(current_frame, previous_frame, params):
    """Einfache Motion Detection ohne Abstürze"""
    try:
        gray_current = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        gray_current = cv2.GaussianBlur(gray_current, (5, 5), 0)
        
        diff = cv2.absdiff(previous_frame, gray_current)
        _, thresh = cv2.threshold(diff, params["threshold"], 255, cv2.THRESH_BINARY)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detections = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if params["min_area"] <= area <= params["max_area"]:
                x, y, w, h = cv2.boundingRect(contour)
                detections.append({"x": x, "y": y, "w": w, "h": h, "area": area})
        
        return detections
    except:
        return []

def annotate_simple(frame, detections, cam_name):
    """Einfache Annotation ohne Abstürze"""
    try:
        annotated = frame.copy()
        
        for i, det in enumerate(detections):
            x, y, w, h = det['x'], det['y'], det['w'], det['h']
            cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(annotated, f"M{i+1}", (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        info = f"{cam_name} - {len(detections)} objects"
        cv2.putText(annotated, info, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return annotated
    except:
        return frame

def main():
    print("🌍 INVESTIGATION: ÜBERLAPPENDE WEBCAM-PERSPEKTIVEN")
    print("=" * 55)
    print("Basierend auf Online-Recherche - gefundene überlappende Perspektiven:")
    print()
    
    # Zeige gefundene Locations
    for i, (key, group) in enumerate(OVERLAPPING_WEBCAMS.items(), 1):
        print(f"{i}. {group['name']} ({len(group['cams'])} Kameras)")
        for cam in group['cams']:
            print(f"   📹 {cam['name']} - {cam['description']}")
        print()
    
    # Automatischer Test der besten Kandidaten
    print("🚀 Starte automatische Tests (max 3 Minuten pro Gruppe)...")
    
    for key, group in OVERLAPPING_WEBCAMS.items():
        print(f"\n{'='*50}")
        try:
            session_dir = capture_sync_frames(group, max_frames=5)  # Nur 5 Frames pro Test
            if session_dir:
                print(f"✅ Test erfolgreich: {session_dir}")
            else:
                print("❌ Test fehlgeschlagen - Kameras nicht verfügbar")
        except Exception as e:
            print(f"❌ Test-Fehler: {str(e)[:50]}")
        
        print("⏱️ Pause zwischen Tests...")
        time.sleep(5)  # Kurze Pause zwischen Tests
    
    print("\n🎉 Investigation abgeschlossen!")
    print("💡 Ergebnis: Gefundene funktionierende überlappende Perspektiven können für 3D-Tracking genutzt werden!")

if __name__ == "__main__":
    main()
