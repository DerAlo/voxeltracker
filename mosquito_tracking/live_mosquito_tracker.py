#!/usr/bin/env python3

import cv2
import numpy as np
import json
import os
import time
from datetime import datetime
import threading
import queue

class LiveMosquitoTracker:
    def __init__(self):
        self.recording = False
        self.frame_queue = queue.Queue(maxsize=100)
        self.detection_data = []
        self.session_start_time = None
        
        # Optimierte Parameter für Mücken
        self.mosquito_params = {
            "threshold": 12,        # Sehr sensitiv für kleinste Bewegungen
            "min_area": 5,          # Extrem kleine Objekte (1-2 Pixel)
            "max_area": 100,        # Mücken sind nie sehr groß
            "blur_kernel": 3,       # Kleiner Blur um Rauschen zu reduzieren
            "morph_kernel": 2,      # Kleine morphologische Operationen
        }
        
    def detect_mosquitos(self, frame, background):
        """
        Erkennt Mücken in einem Frame
        """
        # Konvertiere zu Graustufen
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Slight blur um Sensor-Rauschen zu reduzieren
        gray = cv2.GaussianBlur(gray, (self.mosquito_params["blur_kernel"], 
                                      self.mosquito_params["blur_kernel"]), 0)
        
        # Background Subtraction
        diff = cv2.absdiff(background, gray)
        
        # Threshold für Motion Detection
        _, thresh = cv2.threshold(diff, self.mosquito_params["threshold"], 255, cv2.THRESH_BINARY)
        
        # Morphological operations um Rauschen zu reduzieren
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, 
                                         (self.mosquito_params["morph_kernel"], 
                                          self.mosquito_params["morph_kernel"]))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Finde Konturen
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detections = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Filter basierend auf Größe
            if self.mosquito_params["min_area"] <= area <= self.mosquito_params["max_area"]:
                # Bounding Box und Zentrum
                x, y, w, h = cv2.boundingRect(contour)
                center_x = x + w // 2
                center_y = y + h // 2
                
                # Berechne Konfidenz basierend auf Aspekt-Ratio und Größe
                aspect_ratio = w / h if h > 0 else 0
                confidence = min(1.0, area / 30.0)  # Normalisiere Konfidenz
                
                # Zusätzliche Validierung für Mücken-ähnliche Eigenschaften
                if 0.3 <= aspect_ratio <= 3.0:  # Mücken sind nicht extrem lang oder breit
                    detection = {
                        'x': center_x,
                        'y': center_y,
                        'width': w,
                        'height': h,
                        'area': area,
                        'confidence': confidence,
                        'aspect_ratio': aspect_ratio,
                        'timestamp': time.time()
                    }
                    detections.append(detection)
        
        return detections, thresh
    
    def draw_detections(self, frame, detections):
        """
        Zeichnet Detections auf das Frame
        """
        annotated_frame = frame.copy()
        
        for i, detection in enumerate(detections):
            x, y = detection['x'], detection['y']
            w, h = detection['width'], detection['height']
            confidence = detection['confidence']
            
            # Zeichne Bounding Box
            color = (0, 255, 0) if confidence > 0.5 else (0, 255, 255)  # Grün für hohe, Gelb für niedrige Konfidenz
            cv2.rectangle(annotated_frame, 
                         (x - w//2, y - h//2), 
                         (x + w//2, y + h//2), 
                         color, 2)
            
            # Zeichne Zentrum
            cv2.circle(annotated_frame, (x, y), 3, (0, 0, 255), -1)
            
            # Label mit Konfidenz
            label = f"Mosquito #{i+1} ({confidence:.2f})"
            cv2.putText(annotated_frame, label, 
                       (x - w//2, y - h//2 - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Zeige Statistiken
        stats_text = f"Detected: {len(detections)} | Params: T={self.mosquito_params['threshold']}, A={self.mosquito_params['min_area']}-{self.mosquito_params['max_area']}"
        cv2.putText(annotated_frame, stats_text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return annotated_frame
    
    def save_detection_proof(self, frame, detections, frame_number):
        """
        Speichert Beweis-Bilder von Detections
        """
        if len(detections) > 0:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            proof_dir = f"live_mosquito_proof_{timestamp}"
            os.makedirs(proof_dir, exist_ok=True)
            
            # Speichere annotiertes Frame
            proof_filename = f"{proof_dir}/mosquito_detection_{frame_number:06d}.png"
            annotated_frame = self.draw_detections(frame, detections)
            cv2.imwrite(proof_filename, annotated_frame)
            
            # Speichere Detection-Daten
            detection_data = {
                'frame_number': frame_number,
                'timestamp': time.time(),
                'detections': detections
            }
            self.detection_data.append(detection_data)
            
            return proof_filename
        return None
    
    def run_live_tracking(self, camera_index=0, duration_seconds=60):
        """
        Führt Live-Tracking mit einer Webcam durch
        """
        print(f"🔴 Starte Live-Mücken-Tracking (Kamera {camera_index}, {duration_seconds}s)")
        print("Tipps für beste Ergebnisse:")
        print("  - Gute Beleuchtung verwenden")
        print("  - Kamera ruhig halten")
        print("  - Drücken Sie 'q' zum Beenden")
        print("  - Drücken Sie 's' um Screenshot zu speichern")
        print("  - Drücken Sie '+/-' um Sensitivität anzupassen")
        
        # Öffne Webcam
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            print(f"❌ Kann Kamera {camera_index} nicht öffnen")
            return False
        
        # Setze Auflösung für beste Performance
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        print("📹 Kamera erfolgreich geöffnet")
        print("⏳ Erstelle Hintergrundmodell (5 Sekunden)...")
        
        # Erstelle Hintergrundmodell
        background_frames = []
        for i in range(50):  # 50 Frames für Hintergrund
            ret, frame = cap.read()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.GaussianBlur(gray, (5, 5), 0)
                background_frames.append(gray)
            time.sleep(0.1)
        
        # Berechne mittleren Hintergrund
        background = np.median(background_frames, axis=0).astype(np.uint8)
        print("✅ Hintergrundmodell erstellt")
        
        # Erstelle Session-Verzeichnis
        session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        session_dir = f"live_mosquito_session_{session_id}"
        os.makedirs(session_dir, exist_ok=True)
        
        frame_count = 0
        total_detections = 0
        start_time = time.time()
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("❌ Kann Frame nicht lesen")
                    break
                
                # Erkennung durchführen
                detections, thresh = self.detect_mosquitos(frame, background)
                
                # Zeichne Detections
                display_frame = self.draw_detections(frame, detections)
                
                # Zeige auch Threshold-Bild (klein in der Ecke)
                thresh_small = cv2.resize(thresh, (160, 120))
                thresh_colored = cv2.cvtColor(thresh_small, cv2.COLOR_GRAY2BGR)
                display_frame[10:130, 10:170] = thresh_colored
                cv2.putText(display_frame, "Motion", (15, 145), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                
                # Statistiken updaten
                frame_count += 1
                total_detections += len(detections)
                
                # Zeige Frame
                cv2.imshow('Live Mosquito Tracker', display_frame)
                
                # Speichere bei Detections
                if len(detections) > 0:
                    self.save_detection_proof(frame, detections, frame_count)
                    print(f"Frame {frame_count}: {len(detections)} Mücken erkannt!")
                
                # Check for termination
                elapsed_time = time.time() - start_time
                if elapsed_time > duration_seconds:
                    print(f"⏰ Zeit abgelaufen ({duration_seconds}s)")
                    break
                
                # Keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("🛑 Von Benutzer gestoppt")
                    break
                elif key == ord('s'):
                    # Screenshot speichern
                    screenshot_path = f"{session_dir}/screenshot_{frame_count}.png"
                    cv2.imwrite(screenshot_path, display_frame)
                    print(f"📸 Screenshot gespeichert: {screenshot_path}")
                elif key == ord('+'):
                    # Erhöhe Sensitivität
                    self.mosquito_params["threshold"] = max(5, self.mosquito_params["threshold"] - 2)
                    print(f"🔧 Sensitivität erhöht (Threshold: {self.mosquito_params['threshold']})")
                elif key == ord('-'):
                    # Verringere Sensitivität
                    self.mosquito_params["threshold"] = min(50, self.mosquito_params["threshold"] + 2)
                    print(f"🔧 Sensitivität verringert (Threshold: {self.mosquito_params['threshold']})")
        
        except KeyboardInterrupt:
            print("\\n🛑 Unterbrochen durch Ctrl+C")
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
            
            # Erstelle Abschlussbericht
            total_time = time.time() - start_time
            avg_detections_per_frame = total_detections / frame_count if frame_count > 0 else 0
            
            report = {
                'session_id': session_id,
                'duration_seconds': total_time,
                'total_frames': frame_count,
                'total_detections': total_detections,
                'avg_detections_per_frame': avg_detections_per_frame,
                'fps': frame_count / total_time if total_time > 0 else 0,
                'detection_params': self.mosquito_params,
                'detection_data': self.detection_data
            }
            
            # Speichere Bericht
            report_path = f"{session_dir}/session_report.json"
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"\\n📊 SESSION BEENDET:")
            print(f"   ⏱️  Dauer: {total_time:.1f} Sekunden")
            print(f"   🖼️  Frames: {frame_count}")
            print(f"   🦟 Detections: {total_detections}")
            print(f"   📈 Durchschnitt: {avg_detections_per_frame:.2f} pro Frame")
            print(f"   🎥 FPS: {report['fps']:.1f}")
            print(f"   📁 Session-Daten: {session_dir}")
            
            return True

def main():
    print("🦟 LIVE MÜCKEN-TRACKING MIT WEBCAM")
    print("=" * 50)
    
    tracker = LiveMosquitoTracker()
    
    # Teste verfügbare Kameras
    print("📹 Teste verfügbare Kameras...")
    available_cameras = []
    for i in range(3):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                h, w = frame.shape[:2]
                available_cameras.append((i, f"{w}x{h}"))
                print(f"   ✅ Kamera {i}: {w}x{h}")
            cap.release()
        else:
            print(f"   ❌ Kamera {i}: nicht verfügbar")
    
    if not available_cameras:
        print("❌ Keine funktionierende Kamera gefunden!")
        return
    
    # Verwende erste verfügbare Kamera
    camera_index = available_cameras[0][0]
    print(f"\\n🎯 Verwende Kamera {camera_index}")
    
    # Starte Live-Tracking
    print("\\n⚠️  ANWEISUNGEN:")
    print("   - Positionieren Sie sich in einem gut beleuchteten Bereich")
    print("   - Halten Sie die Kamera ruhig")
    print("   - Warten Sie auf Mücken oder bewegen Sie kleine Objekte vor der Kamera")
    print("   - Das System ist auf 1-3 Pixel große Objekte optimiert")
    
    input("\\nDrücken Sie Enter um zu starten...")
    
    # Starte 60 Sekunden Live-Tracking
    success = tracker.run_live_tracking(camera_index, duration_seconds=60)
    
    if success:
        print("\\n✅ Live-Tracking erfolgreich abgeschlossen!")
        print("📁 Überprüfen Sie die erstellten Session-Verzeichnisse für Beweis-Bilder")
    else:
        print("❌ Live-Tracking fehlgeschlagen")

if __name__ == "__main__":
    main()
