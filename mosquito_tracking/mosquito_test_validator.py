#!/usr/bin/env python3

import cv2
import numpy as np
import json
import os
import time
from datetime import datetime
import glob

class MosquitoTestValidator:
    def __init__(self):
        self.results = {
            'test_timestamp': datetime.now().isoformat(),
            'tests_performed': [],
            'detection_stats': {},
            'proof_files': []
        }
        
    def test_mosquito_detection(self, test_dir, profile_name="Mosquito 🦟"):
        """
        Testet Mückenerkennung mit den erstellten Testdaten
        """
        print(f"\n🔬 Teste Mückenerkennung in: {test_dir}")
        
        # Lade Metadaten
        metadata_path = os.path.join(test_dir, "metadata.json")
        if not os.path.exists(metadata_path):
            print(f"❌ Keine metadata.json in {test_dir} gefunden")
            return False
            
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Lade Bilder
        image_files = glob.glob(os.path.join(test_dir, "*.png"))
        image_files.sort()
        
        if len(image_files) == 0:
            print(f"❌ Keine Bilder in {test_dir} gefunden")
            return False
            
        print(f"📁 Gefunden: {len(image_files)} Bilder")
        
        # Motion Detection Setup (wie im Mosquito-Profil)
        detection_params = {
            "threshold": 15,        # Sehr sensitiv für kleine Bewegungen
            "min_area": 10,         # Sehr kleine Objekte
            "max_area": 150,        # Falsch-Positive verhindern
        }
        
        # Erstelle Output-Verzeichnis für Beweise
        proof_dir = f"proof_{test_dir}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(proof_dir, exist_ok=True)
        
        detections = []
        previous_frame = None
        
        for i, img_path in enumerate(image_files):
            img = cv2.imread(img_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            if previous_frame is not None:
                # Motion Detection
                diff = cv2.absdiff(previous_frame, gray)
                _, thresh = cv2.threshold(diff, detection_params["threshold"], 255, cv2.THRESH_BINARY)
                
                # Morphological operations um Rauschen zu reduzieren
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
                thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
                thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
                
                # Finde Konturen
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                frame_detections = []
                
                # Analysiere jede Kontur
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if detection_params["min_area"] <= area <= detection_params["max_area"]:
                        # Bounding Box
                        x, y, w, h = cv2.boundingRect(contour)
                        center_x = x + w // 2
                        center_y = y + h // 2
                        
                        # Speichere Detection
                        detection = {
                            'frame': i,
                            'x': center_x,
                            'y': center_y,
                            'area': area,
                            'confidence': min(1.0, area / 50.0)  # Einfache Konfidenz basierend auf Größe
                        }
                        frame_detections.append(detection)
                        
                        # Zeichne Detection auf Bild
                        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        cv2.circle(img, (center_x, center_y), 3, (0, 0, 255), -1)
                        cv2.putText(img, f"Mosquito #{len(frame_detections)}", 
                                  (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                detections.extend(frame_detections)
                
                # Speichere annotiertes Bild als Beweis
                proof_filename = f"detection_frame_{i:03d}.png"
                proof_path = os.path.join(proof_dir, proof_filename)
                cv2.imwrite(proof_path, img)
                
                # Zeige auch Difference-Bild
                diff_filename = f"diff_frame_{i:03d}.png"
                diff_path = os.path.join(proof_dir, diff_filename)
                cv2.imwrite(diff_path, thresh)
                
                print(f"Frame {i}: {len(frame_detections)} Mücken erkannt")
                
            previous_frame = gray.copy()
        
        # Statistiken
        total_detections = len(detections)
        avg_detections_per_frame = total_detections / len(image_files) if image_files else 0
        
        test_result = {
            'test_name': f'mosquito_detection_{test_dir}',
            'profile_used': profile_name,
            'total_frames': len(image_files),
            'total_detections': total_detections,
            'avg_detections_per_frame': avg_detections_per_frame,
            'detection_params': detection_params,
            'proof_directory': proof_dir,
            'success': total_detections > 0
        }
        
        self.results['tests_performed'].append(test_result)
        self.results['proof_files'].append(proof_dir)
        
        print(f"\n✅ Test abgeschlossen!")
        print(f"📊 Statistiken:")
        print(f"   - Frames verarbeitet: {len(image_files)}")
        print(f"   - Gesamte Detections: {total_detections}")
        print(f"   - Durchschnitt pro Frame: {avg_detections_per_frame:.2f}")
        print(f"📁 Beweise gespeichert in: {proof_dir}")
        
        return True
    
    def create_video_proof(self, proof_dir, output_name="mosquito_detection_proof.mp4"):
        """
        Erstellt ein Video aus den Detection-Frames als Beweis
        """
        print(f"\n🎬 Erstelle Video-Beweis...")
        
        detection_images = glob.glob(os.path.join(proof_dir, "detection_frame_*.png"))
        detection_images.sort()
        
        if len(detection_images) == 0:
            print("❌ Keine Detection-Bilder für Video gefunden")
            return False
            
        # Lese erstes Bild um Dimensionen zu bekommen
        first_img = cv2.imread(detection_images[0])
        height, width, _ = first_img.shape
        
        # Video Writer setup
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_path = os.path.join(proof_dir, output_name)
        out = cv2.VideoWriter(video_path, fourcc, 10.0, (width, height))  # 10 FPS
        
        for img_path in detection_images:
            img = cv2.imread(img_path)
            out.write(img)
        
        out.release()
        
        print(f"✅ Video erstellt: {video_path}")
        self.results['proof_files'].append(video_path)
        
        return True
    
    def test_webcam_compatibility(self):
        """
        Testet ob normale Webcams erkannt werden
        """
        print(f"\n📹 Teste Webcam-Kompatibilität...")
        
        webcam_test = {
            'test_name': 'webcam_compatibility',
            'available_cameras': [],
            'working_cameras': []
        }
        
        # Teste bis zu 3 Kamera-Indizes
        for camera_idx in range(3):
            try:
                cap = cv2.VideoCapture(camera_idx)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        height, width = frame.shape[:2]
                        webcam_info = {
                            'camera_index': camera_idx,
                            'resolution': f"{width}x{height}",
                            'working': True
                        }
                        webcam_test['working_cameras'].append(webcam_info)
                        print(f"✅ Kamera {camera_idx}: {width}x{height} - funktioniert")
                    else:
                        print(f"❌ Kamera {camera_idx}: kann nicht lesen")
                    cap.release()
                else:
                    print(f"❌ Kamera {camera_idx}: kann nicht öffnen")
            except Exception as e:
                print(f"❌ Kamera {camera_idx}: Fehler - {e}")
        
        webcam_test['success'] = len(webcam_test['working_cameras']) > 0
        self.results['tests_performed'].append(webcam_test)
        
        return webcam_test['success']
    
    def generate_report(self):
        """
        Erstellt einen detaillierten Testbericht
        """
        report_filename = f"mosquito_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Erstelle auch einen lesbaren Bericht
        readable_report = f"mosquito_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(readable_report, 'w', encoding='utf-8') as f:
            f.write("🔬 MÜCKEN-TRACKING SYSTEM TEST BERICHT\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Test-Zeitpunkt: {self.results['test_timestamp']}\n\n")
            
            for test in self.results['tests_performed']:
                f.write(f"Test: {test['test_name']}\n")
                f.write(f"Status: {'✅ ERFOLGREICH' if test['success'] else '❌ FEHLGESCHLAGEN'}\n")
                
                if 'total_detections' in test:
                    f.write(f"Detections: {test['total_detections']}\n")
                    f.write(f"Frames: {test['total_frames']}\n")
                    f.write(f"Durchschnitt: {test.get('avg_detections_per_frame', 0):.2f}\n")
                
                if 'working_cameras' in test:
                    f.write(f"Funktionierende Webcams: {len(test['working_cameras'])}\n")
                
                f.write("\n" + "-" * 30 + "\n\n")
            
            f.write(f"Beweis-Dateien erstellt:\n")
            for proof_file in self.results['proof_files']:
                f.write(f"  - {proof_file}\n")
        
        print(f"\n📋 Testbericht erstellt:")
        print(f"   - {report_filename} (JSON)")
        print(f"   - {readable_report} (Text)")

def main():
    print("🦟 MÜCKEN-TRACKING SYSTEM VALIDIERUNG")
    print("=" * 50)
    
    validator = MosquitoTestValidator()
    
    # Test 1: Mücken-Detection mit ersten Testdaten
    if os.path.exists("mosquito_test"):
        success1 = validator.test_mosquito_detection("mosquito_test")
        if success1:
            # Erstelle Video-Beweis
            proof_dirs = [d for d in os.listdir('.') if d.startswith('proof_mosquito_test_')]
            if proof_dirs:
                validator.create_video_proof(proof_dirs[-1])
    
    # Test 2: Realistische Mücken-Detection
    if os.path.exists("realistic_mosquito_test"):
        success2 = validator.test_mosquito_detection("realistic_mosquito_test")
        if success2:
            # Erstelle Video-Beweis
            proof_dirs = [d for d in os.listdir('.') if d.startswith('proof_realistic_mosquito_test_')]
            if proof_dirs:
                validator.create_video_proof(proof_dirs[-1])
    
    # Test 3: Webcam-Kompatibilität
    validator.test_webcam_compatibility()
    
    # Generiere finalen Bericht
    validator.generate_report()
    
    print("\n🎉 ALLE TESTS ABGESCHLOSSEN!")
    print("📁 Überprüfen Sie die erstellten Proof-Verzeichnisse und Videos")

if __name__ == "__main__":
    main()
