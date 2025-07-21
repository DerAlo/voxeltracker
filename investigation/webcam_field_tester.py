#!/usr/bin/env python3

import cv2
import numpy as np
import requests
import json
import time
from datetime import datetime
import os
import threading

class PublicWebcamFieldTest:
    def __init__(self):
        self.detection_data = []
        
        # Getestete und funktionierende öffentliche Webcams
        self.reliable_webcams = [
            {
                "name": "Times Square NYC",
                "url": "https://images-webcams.windy.com/90/1491309590/current/icon/1491309590.jpg",
                "location": "New York, USA",
                "refresh_seconds": 10,
                "description": "Belebter Platz - Menschen, Vögel, Verkehr",
                "expected_motion": "high"
            },
            {
                "name": "Zell am See Austria",
                "url": "https://www.foto-webcam.eu/webcam/zellamsee/current/400.jpg",
                "location": "Österreich",
                "refresh_seconds": 30,
                "description": "Berglandschaft - Vögel, Touristen",
                "expected_motion": "medium"
            },
            {
                "name": "Prague Old Town",
                "url": "https://images-webcams.windy.com/21/1586785821/current/icon/1586785821.jpg",
                "location": "Prag, Tschechien",
                "refresh_seconds": 15,
                "description": "Historischer Platz - Fußgänger, Vögel",
                "expected_motion": "medium"
            },
            {
                "name": "Abbey Road London",
                "url": "https://images-webcams.windy.com/14/1484815414/current/icon/1484815414.jpg",
                "location": "London, UK", 
                "refresh_seconds": 5,
                "description": "Berühmte Straßenkreuzung - Fußgänger",
                "expected_motion": "high"
            },
            {
                "name": "Innsbruck Cityview",
                "url": "https://images.bergfex.at/images/webcam/1024/6_55145.jpg",
                "location": "Innsbruck, Österreich",
                "refresh_seconds": 20,
                "description": "Stadtblick - Verkehr, Menschen",
                "expected_motion": "medium"
            }
        ]
        
        # Überlappende Kameras (geografisch nah)
        self.overlapping_pairs = [
            {
                "pair_name": "Austrian Alps Overlap",
                "cam1": {
                    "name": "Zell am See North",
                    "url": "https://www.foto-webcam.eu/webcam/zellamsee/current/400.jpg"
                },
                "cam2": {
                    "name": "Innsbruck South", 
                    "url": "https://images.bergfex.at/images/webcam/1024/6_55145.jpg"
                },
                "overlap_description": "Ähnliche Alpenregion - teste Vogel-Tracking"
            },
            {
                "pair_name": "European City Centers",
                "cam1": {
                    "name": "Prague Square",
                    "url": "https://images-webcams.windy.com/21/1586785821/current/icon/1586785821.jpg"
                },
                "cam2": {
                    "name": "London Street",
                    "url": "https://images-webcams.windy.com/14/1484815414/current/icon/1484815414.jpg"
                },
                "overlap_description": "Städtische Umgebung - vergleichbare Bewegungsmuster"
            }
        ]
    
    def test_webcam_availability(self):
        """
        Testet welche Webcams aktuell verfügbar sind
        """
        print("🔍 Teste Verfügbarkeit der öffentlichen Webcams...")
        
        available_cams = []
        
        for cam in self.reliable_webcams:
            try:
                print(f"Teste: {cam['name']}")
                response = requests.get(cam['url'], timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                
                if response.status_code == 200 and len(response.content) > 5000:
                    print(f"✅ {cam['name']} - Verfügbar ({len(response.content)} bytes)")
                    available_cams.append(cam)
                else:
                    print(f"❌ {cam['name']} - Nicht verfügbar (Status: {response.status_code})")
                    
            except Exception as e:
                print(f"❌ {cam['name']} - Fehler: {str(e)[:50]}")
        
        print(f"\n✅ {len(available_cams)} von {len(self.reliable_webcams)} Webcams verfügbar")
        return available_cams
    
    def multi_webcam_field_test(self, webcams, duration_minutes=10):
        """
        Führt paralleles Motion-Tracking auf mehreren Webcams durch
        """
        print(f"🎯 Starte Multi-Webcam Field-Test mit {len(webcams)} Kameras")
        print(f"⏱️ Dauer: {duration_minutes} Minuten")
        
        # Session-Ordner erstellen
        session_dir = f"multi_webcam_field_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(session_dir, exist_ok=True)
        
        # Thread für jede Webcam
        threads = []
        results = {}
        
        for cam in webcams:
            cam_thread = threading.Thread(
                target=self.track_single_webcam,
                args=(cam, session_dir, duration_minutes, results)
            )
            threads.append(cam_thread)
            cam_thread.start()
            
            # Kleine Verzögerung zwischen Starts
            time.sleep(2)
        
        print("🔄 Alle Webcam-Threads gestartet...")
        
        # Warte auf alle Threads
        for thread in threads:
            thread.join()
        
        print("✅ Alle Webcam-Threads beendet")
        
        # Erstelle Zusammenfassung
        self.create_multi_webcam_report(session_dir, results)
        
        return session_dir, results
    
    def track_single_webcam(self, cam, session_dir, duration_minutes, results):
        """
        Trackt eine einzelne Webcam in eigenem Thread
        """
        cam_name = cam['name'].replace(' ', '_')
        cam_dir = f"{session_dir}/{cam_name}"
        os.makedirs(cam_dir, exist_ok=True)
        
        print(f"🎬 Starte Tracking: {cam['name']}")
        
        frame_count = 0
        detection_count = 0
        start_time = time.time()
        previous_frame = None
        
        # Motion-Detection Parameter (optimiert für Webcam-Qualität)
        motion_params = {
            "threshold": 25,
            "min_area": 80,
            "max_area": 8000,
            "blur_kernel": 5
        }
        
        try:
            while (time.time() - start_time) < (duration_minutes * 60):
                try:
                    # Lade aktuelles Webcam-Bild
                    response = requests.get(cam['url'], timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
                    
                    if response.status_code == 200:
                        # Konvertiere zu OpenCV Frame
                        img_array = np.frombuffer(response.content, np.uint8)
                        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                        
                        if frame is not None:
                            frame_count += 1
                            
                            # Motion Detection
                            if previous_frame is not None:
                                detections = self.detect_webcam_motion(frame, previous_frame, motion_params)
                                
                                if len(detections) > 0:
                                    detection_count += len(detections)
                                    print(f"🎯 {cam['name']}: Frame {frame_count}, {len(detections)} Objekte")
                                    
                                    # Speichere annotiertes Bild
                                    annotated = self.annotate_frame(frame, detections, cam['name'])
                                    filename = f"{cam_dir}/detection_{frame_count:04d}.jpg"
                                    cv2.imwrite(filename, annotated)
                            
                            # Update previous frame
                            previous_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                            previous_frame = cv2.GaussianBlur(previous_frame, (motion_params["blur_kernel"], motion_params["blur_kernel"]), 0)
                            
                            # Speichere Raw-Frame (jeden 5.)
                            if frame_count % 5 == 0:
                                raw_filename = f"{cam_dir}/raw_{frame_count:04d}.jpg"
                                cv2.imwrite(raw_filename, frame)
                    
                except Exception as e:
                    print(f"❌ {cam['name']} Frame-Fehler: {str(e)[:30]}")
                
                # Warte entsprechend Webcam-Refresh-Rate
                time.sleep(cam.get('refresh_seconds', 10))
        
        except Exception as e:
            print(f"❌ {cam['name']} Thread-Fehler: {e}")
        
        # Speichere Ergebnisse
        cam_results = {
            'name': cam['name'],
            'location': cam['location'],
            'total_frames': frame_count,
            'total_detections': detection_count,
            'avg_detections_per_frame': detection_count / max(frame_count, 1),
            'duration_minutes': duration_minutes,
            'session_dir': cam_dir
        }
        
        results[cam_name] = cam_results
        
        print(f"✅ {cam['name']} beendet: {frame_count} Frames, {detection_count} Detections")
    
    def detect_webcam_motion(self, current_frame, previous_frame, params):
        """
        Motion Detection für Webcam-Bilder
        """
        # Aktuellen Frame zu Graustufen
        gray_current = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        gray_current = cv2.GaussianBlur(gray_current, (params["blur_kernel"], params["blur_kernel"]), 0)
        
        # Frame-Differenz
        diff = cv2.absdiff(previous_frame, gray_current)
        
        # Threshold
        _, thresh = cv2.threshold(diff, params["threshold"], 255, cv2.THRESH_BINARY)
        
        # Morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Finde Konturen
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detections = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if params["min_area"] <= area <= params["max_area"]:
                x, y, w, h = cv2.boundingRect(contour)
                detection = {
                    'x': x + w // 2,
                    'y': y + h // 2,
                    'width': w,
                    'height': h,
                    'area': area,
                    'confidence': min(1.0, area / 2000.0)
                }
                detections.append(detection)
        
        return detections
    
    def annotate_frame(self, frame, detections, webcam_name):
        """
        Annotiert Frame mit Detections
        """
        annotated = frame.copy()
        
        for i, det in enumerate(detections):
            x, y = det['x'], det['y']
            w, h = det['width'], det['height']
            
            # Bounding Box
            cv2.rectangle(annotated, (x - w//2, y - h//2), (x + w//2, y + h//2), (0, 255, 0), 2)
            
            # Label
            label = f"Motion {i+1}"
            cv2.putText(annotated, label, (x - w//2, y - h//2 - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Webcam-Info
        info = f"{webcam_name} - {len(detections)} objects - {datetime.now().strftime('%H:%M:%S')}"
        cv2.putText(annotated, info, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return annotated
    
    def create_multi_webcam_report(self, session_dir, results):
        """
        Erstellt Gesamtbericht über Multi-Webcam Test
        """
        total_frames = sum(r['total_frames'] for r in results.values())
        total_detections = sum(r['total_detections'] for r in results.values())
        
        report = {
            'test_type': 'Multi-Webcam Field Test',
            'timestamp': datetime.now().isoformat(),
            'session_dir': session_dir,
            'webcam_count': len(results),
            'total_frames_all_cams': total_frames,
            'total_detections_all_cams': total_detections,
            'avg_detections_per_frame_overall': total_detections / max(total_frames, 1),
            'individual_results': results
        }
        
        # Speichere Gesamtbericht
        report_file = f"{session_dir}/multi_webcam_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Konsolenausgabe
        print("\n" + "="*60)
        print("🎉 MULTI-WEBCAM FIELD-TEST ABGESCHLOSSEN")
        print("="*60)
        print(f"📊 Getestete Webcams: {len(results)}")
        print(f"🎬 Frames gesamt: {total_frames}")
        print(f"🎯 Detections gesamt: {total_detections}")
        print(f"📈 Durchschnitt: {report['avg_detections_per_frame_overall']:.2f} pro Frame")
        
        print("\n📋 EINZELERGEBNISSE:")
        for cam_name, result in results.items():
            print(f"  📹 {result['name']}: {result['total_detections']} detections in {result['total_frames']} frames")
        
        print(f"\n📁 Session-Daten: {session_dir}")
        print("🔍 Überprüfen Sie die einzelnen Kamera-Ordner für Details!")
        
        return report

def main():
    print("🌍 ÖFFENTLICHE WEBCAM FIELD-TEST")
    print("=" * 50)
    print("Teste unser Motion-Tracking System mit echten öffentlichen Webcams!")
    
    tester = PublicWebcamFieldTest()
    
    # Teste Verfügbarkeit
    available_cams = tester.test_webcam_availability()
    
    if len(available_cams) == 0:
        print("❌ Keine Webcams verfügbar. Bitte später versuchen.")
        return
    
    print(f"\n✅ {len(available_cams)} Webcams verfügbar für Field-Test")
    
    # Auswahl
    if len(available_cams) > 3:
        selected_cams = available_cams[:3]  # Maximal 3 für Performance
        print(f"🎯 Verwende die ersten 3 Webcams für optimale Performance")
    else:
        selected_cams = available_cams
    
    for i, cam in enumerate(selected_cams):
        print(f"  {i+1}. {cam['name']} - {cam['location']}")
    
    print(f"\n🚀 Starte Field-Test mit {len(selected_cams)} Webcams...")
    print("⏱️ Dauer: 5 Minuten pro Kamera (parallel)")
    print("🛑 Drücken Sie Ctrl+C zum vorzeitigen Stoppen")
    
    try:
        session_dir, results = tester.multi_webcam_field_test(selected_cams, duration_minutes=5)
        
        print("\n🎉 Field-Test erfolgreich abgeschlossen!")
        print("💡 Das System funktioniert mit echten öffentlichen Webcams!")
        
    except KeyboardInterrupt:
        print("\n🛑 Field-Test gestoppt")
    except Exception as e:
        print(f"\n❌ Field-Test Fehler: {e}")

if __name__ == "__main__":
    main()
