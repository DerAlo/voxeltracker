#!/usr/bin/env python3

import cv2
import numpy as np
import requests
import json
import time
from datetime import datetime
import os
import math

class OverlappingCameraFinder:
    def __init__(self):
        # Geografische Webcam-Datenbank mit Koordinaten
        self.geo_webcams = [
            {
                "name": "Times Square South",
                "url": "https://images-webcams.windy.com/90/1491309590/current/icon/1491309590.jpg",
                "lat": 40.7580, "lng": -73.9855,
                "direction": "north", "fov": 60,
                "description": "Times Square Richtung Norden"
            },
            {
                "name": "Times Square North", 
                "url": "https://images-webcams.windy.com/91/1491309591/current/icon/1491309591.jpg",
                "lat": 40.7590, "lng": -73.9850,
                "direction": "south", "fov": 60,
                "description": "Times Square Richtung Süden"
            },
            {
                "name": "Prague Castle View",
                "url": "https://images-webcams.windy.com/21/1586785821/current/icon/1586785821.jpg", 
                "lat": 50.0755, "lng": 14.4378,
                "direction": "east", "fov": 90,
                "description": "Prager Burg Blick nach Osten"
            },
            {
                "name": "Prague Bridge View",
                "url": "https://images-webcams.windy.com/22/1586785822/current/icon/1586785822.jpg",
                "lat": 50.0865, "lng": 14.4114,
                "direction": "west", "fov": 70,
                "description": "Karlsbrücke Blick nach Westen"
            },
            {
                "name": "London Eye South",
                "url": "https://images-webcams.windy.com/14/1484815414/current/icon/1484815414.jpg",
                "lat": 51.5033, "lng": -0.1195,
                "direction": "north", "fov": 80,
                "description": "London Eye Richtung Norden"
            },
            {
                "name": "London Bridge North",
                "url": "https://images-webcams.windy.com/15/1484815415/current/icon/1484815415.jpg",
                "lat": 51.5074, "lng": -0.0877,
                "direction": "south", "fov": 75,
                "description": "Tower Bridge Richtung Süden"
            }
        ]
    
    def calculate_distance(self, lat1, lng1, lat2, lng2):
        """
        Berechnet Entfernung zwischen zwei Koordinaten in km
        """
        R = 6371  # Erdradius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lng/2) * math.sin(delta_lng/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance
    
    def find_overlapping_pairs(self, max_distance_km=2.0):
        """
        Findet Kamera-Paare mit potentiell überlappenden Sichtfeldern
        """
        print(f"🔍 Suche nach überlappenden Kamera-Paaren (max {max_distance_km}km Entfernung)")
        
        overlapping_pairs = []
        
        for i, cam1 in enumerate(self.geo_webcams):
            for j, cam2 in enumerate(self.geo_webcams[i+1:], i+1):
                distance = self.calculate_distance(
                    cam1['lat'], cam1['lng'], 
                    cam2['lat'], cam2['lng']
                )
                
                if distance <= max_distance_km:
                    # Berechne potentielle Überlappung basierend auf Richtung und FOV
                    overlap_score = self.calculate_overlap_probability(cam1, cam2, distance)
                    
                    if overlap_score > 0.3:  # Mindest-Überlappungswahrscheinlichkeit
                        pair = {
                            'cam1': cam1,
                            'cam2': cam2,
                            'distance_km': distance,
                            'overlap_score': overlap_score,
                            'test_priority': 'high' if overlap_score > 0.7 else 'medium'
                        }
                        overlapping_pairs.append(pair)
                        
                        print(f"✅ Überlappung gefunden:")
                        print(f"   📹 {cam1['name']} ↔ {cam2['name']}")
                        print(f"   📏 Entfernung: {distance:.2f}km")
                        print(f"   🎯 Überlappung: {overlap_score:.2f}")
        
        # Sortiere nach Überlappungswahrscheinlichkeit
        overlapping_pairs.sort(key=lambda x: x['overlap_score'], reverse=True)
        
        print(f"\n✅ {len(overlapping_pairs)} überlappende Kamera-Paare gefunden")
        return overlapping_pairs
    
    def calculate_overlap_probability(self, cam1, cam2, distance):
        """
        Berechnet Wahrscheinlichkeit einer Sichtfeld-Überlappung
        """
        # Basis-Score basierend auf Entfernung
        distance_score = max(0, 1 - (distance / 2.0))  # Je näher, desto besser
        
        # Richtungs-Score (gegenüberliegende Richtungen = höhere Überlappung)
        direction_map = {'north': 0, 'east': 90, 'south': 180, 'west': 270}
        
        dir1 = direction_map.get(cam1.get('direction', 'north'), 0)
        dir2 = direction_map.get(cam2.get('direction', 'north'), 0)
        
        angle_diff = abs(dir1 - dir2)
        if angle_diff > 180:
            angle_diff = 360 - angle_diff
        
        # Gegenüberliegende Richtungen (180°) sind ideal
        direction_score = max(0, 1 - abs(angle_diff - 180) / 180)
        
        # FOV-Score (größeres Sichtfeld = höhere Überlappung)
        avg_fov = (cam1.get('fov', 60) + cam2.get('fov', 60)) / 2
        fov_score = min(1.0, avg_fov / 90)  # Normalisiert auf 90° max
        
        # Gesamt-Score
        overlap_score = (distance_score * 0.4 + direction_score * 0.4 + fov_score * 0.2)
        
        return overlap_score
    
    def test_overlapping_pair(self, pair, duration_minutes=10):
        """
        Testet ein überlappended Kamera-Paar synchron
        """
        cam1, cam2 = pair['cam1'], pair['cam2']
        
        print(f"🎯 Teste überlappende Kameras:")
        print(f"   📹 {cam1['name']} ↔ {cam2['name']}")
        print(f"   📏 Entfernung: {pair['distance_km']:.2f}km")
        print(f"   🎯 Überlappung: {pair['overlap_score']:.2f}")
        
        # Session-Ordner
        session_dir = f"overlap_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(session_dir, exist_ok=True)
        
        # Synchroner Test beider Kameras
        results = self.synchronous_dual_capture(cam1, cam2, session_dir, duration_minutes)
        
        # Analysiere Überlappung
        overlap_analysis = self.analyze_motion_overlap(results, session_dir)
        
        return session_dir, results, overlap_analysis
    
    def synchronous_dual_capture(self, cam1, cam2, session_dir, duration_minutes):
        """
        Synchrone Aufnahme beider Kameras
        """
        print("📸 Starte synchrone Dual-Capture...")
        
        cam1_dir = f"{session_dir}/cam1_{cam1['name'].replace(' ', '_')}"
        cam2_dir = f"{session_dir}/cam2_{cam2['name'].replace(' ', '_')}"
        os.makedirs(cam1_dir, exist_ok=True)
        os.makedirs(cam2_dir, exist_ok=True)
        
        results = {
            'cam1': {'name': cam1['name'], 'frames': [], 'detections': []},
            'cam2': {'name': cam2['name'], 'frames': [], 'detections': []}
        }
        
        start_time = time.time()
        frame_count = 0
        
        # Motion-Detection Parameter
        motion_params = {
            "threshold": 25,
            "min_area": 100,
            "max_area": 5000,
            "blur_kernel": 5
        }
        
        prev_frame1, prev_frame2 = None, None
        
        try:
            while (time.time() - start_time) < (duration_minutes * 60):
                frame_count += 1
                timestamp = time.time()
                
                # Synchrone Captures
                frame1 = self.capture_webcam_frame(cam1['url'])
                frame2 = self.capture_webcam_frame(cam2['url'])
                
                if frame1 is not None and frame2 is not None:
                    # Speichere Rohbilder
                    cv2.imwrite(f"{cam1_dir}/raw_{frame_count:04d}.jpg", frame1)
                    cv2.imwrite(f"{cam2_dir}/raw_{frame_count:04d}.jpg", frame2)
                    
                    # Motion Detection
                    detections1 = []
                    detections2 = []
                    
                    if prev_frame1 is not None:
                        detections1 = self.detect_motion_webcam(frame1, prev_frame1, motion_params)
                    if prev_frame2 is not None:
                        detections2 = self.detect_motion_webcam(frame2, prev_frame2, motion_params)
                    
                    # Speichere Detections
                    if len(detections1) > 0:
                        annotated1 = self.annotate_frame_with_detections(frame1, detections1, cam1['name'])
                        cv2.imwrite(f"{cam1_dir}/detection_{frame_count:04d}.jpg", annotated1)
                    
                    if len(detections2) > 0:
                        annotated2 = self.annotate_frame_with_detections(frame2, detections2, cam2['name'])
                        cv2.imwrite(f"{cam2_dir}/detection_{frame_count:04d}.jpg", annotated2)
                    
                    # Speichere Resultate
                    results['cam1']['frames'].append(frame_count)
                    results['cam1']['detections'].append({
                        'frame': frame_count,
                        'timestamp': timestamp,
                        'count': len(detections1),
                        'objects': detections1
                    })
                    
                    results['cam2']['frames'].append(frame_count)
                    results['cam2']['detections'].append({
                        'frame': frame_count,
                        'timestamp': timestamp, 
                        'count': len(detections2),
                        'objects': detections2
                    })
                    
                    # Status
                    if frame_count % 5 == 0:
                        det1_count = sum(d['count'] for d in results['cam1']['detections'])
                        det2_count = sum(d['count'] for d in results['cam2']['detections'])
                        print(f"📊 Frame {frame_count}: Cam1={det1_count} Det, Cam2={det2_count} Det")
                    
                    # Update previous frames
                    prev_frame1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
                    prev_frame2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
                    prev_frame1 = cv2.GaussianBlur(prev_frame1, (motion_params["blur_kernel"], motion_params["blur_kernel"]), 0)
                    prev_frame2 = cv2.GaussianBlur(prev_frame2, (motion_params["blur_kernel"], motion_params["blur_kernel"]), 0)
                
                # Warte zwischen Captures
                time.sleep(15)  # 15 Sekunden zwischen synchronen Captures
        
        except KeyboardInterrupt:
            print("🛑 Dual-Capture gestoppt")
        
        print(f"✅ Dual-Capture beendet: {frame_count} synchrone Frames")
        return results
    
    def capture_webcam_frame(self, url):
        """
        Erfasst einzelnen Frame von Webcam-URL
        """
        try:
            response = requests.get(url, timeout=8, headers={'User-Agent': 'Mozilla/5.0'})
            if response.status_code == 200:
                img_array = np.frombuffer(response.content, np.uint8)
                frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                return frame
        except Exception:
            pass
        return None
    
    def detect_motion_webcam(self, current_frame, previous_frame, params):
        """
        Motion Detection zwischen zwei Frames
        """
        gray_current = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        gray_current = cv2.GaussianBlur(gray_current, (params["blur_kernel"], params["blur_kernel"]), 0)
        
        diff = cv2.absdiff(previous_frame, gray_current)
        _, thresh = cv2.threshold(diff, params["threshold"], 255, cv2.THRESH_BINARY)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detections = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if params["min_area"] <= area <= params["max_area"]:
                x, y, w, h = cv2.boundingRect(contour)
                detection = {
                    'x': x + w // 2, 'y': y + h // 2,
                    'width': w, 'height': h, 'area': area
                }
                detections.append(detection)
        
        return detections
    
    def annotate_frame_with_detections(self, frame, detections, cam_name):
        """
        Annotiert Frame mit Detections
        """
        annotated = frame.copy()
        
        for i, det in enumerate(detections):
            x, y = det['x'], det['y']
            w, h = det['width'], det['height']
            
            cv2.rectangle(annotated, (x - w//2, y - h//2), (x + w//2, y + h//2), (0, 255, 0), 2)
            cv2.putText(annotated, f"M{i+1}", (x - w//2, y - h//2 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        info = f"{cam_name} - {len(detections)} objects - {datetime.now().strftime('%H:%M:%S')}"
        cv2.putText(annotated, info, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return annotated
    
    def analyze_motion_overlap(self, results, session_dir):
        """
        Analysiert Bewegungsüberlappung zwischen den Kameras
        """
        print("🔍 Analysiere Bewegungsüberlappung...")
        
        cam1_detections = results['cam1']['detections']
        cam2_detections = results['cam2']['detections']
        
        # Zeitliche Korrelation der Detections
        correlation_score = self.calculate_temporal_correlation(cam1_detections, cam2_detections)
        
        # Statistiken
        total_det1 = sum(d['count'] for d in cam1_detections)
        total_det2 = sum(d['count'] for d in cam2_detections)
        
        analysis = {
            'cam1_total_detections': total_det1,
            'cam2_total_detections': total_det2,
            'temporal_correlation': correlation_score,
            'overlap_quality': 'high' if correlation_score > 0.7 else 'medium' if correlation_score > 0.4 else 'low',
            'sync_frames': len(cam1_detections)
        }
        
        # Speichere Analyse
        with open(f"{session_dir}/overlap_analysis.json", 'w') as f:
            json.dump(analysis, f, indent=2)
        
        print("📊 ÜBERLAPPUNGSANALYSE:")
        print(f"   🎯 Kamera 1 Detections: {total_det1}")
        print(f"   🎯 Kamera 2 Detections: {total_det2}")
        print(f"   ⏱️ Zeitliche Korrelation: {correlation_score:.3f}")
        print(f"   🏆 Überlappungsqualität: {analysis['overlap_quality']}")
        
        return analysis
    
    def calculate_temporal_correlation(self, det1_list, det2_list):
        """
        Berechnet zeitliche Korrelation zwischen Detection-Listen
        """
        if len(det1_list) == 0 or len(det2_list) == 0:
            return 0.0
        
        # Erstelle Zeitreihen der Detection-Counts
        timestamps1 = [d['timestamp'] for d in det1_list]
        timestamps2 = [d['timestamp'] for d in det2_list]
        counts1 = [d['count'] for d in det1_list]
        counts2 = [d['count'] for d in det2_list]
        
        # Finde gemeinsame Zeitfenster (vereinfacht)
        min_len = min(len(counts1), len(counts2))
        if min_len < 3:
            return 0.0
        
        # Korrelationskoeffizient (vereinfacht)
        counts1_short = counts1[:min_len]
        counts2_short = counts2[:min_len]
        
        if max(counts1_short) == 0 and max(counts2_short) == 0:
            return 1.0  # Beide haben keine Detections = perfekte Korrelation
        
        # Pearson-ähnliche Korrelation
        mean1, mean2 = np.mean(counts1_short), np.mean(counts2_short)
        
        numerator = sum((a - mean1) * (b - mean2) for a, b in zip(counts1_short, counts2_short))
        denominator = (sum((a - mean1) ** 2 for a in counts1_short) * 
                      sum((b - mean2) ** 2 for b in counts2_short)) ** 0.5
        
        if denominator == 0:
            return 0.0
        
        correlation = numerator / denominator
        return max(0.0, correlation)  # Nur positive Korrelation interessant

def main():
    print("🌍 ÜBERLAPPENDE WEBCAM-PERSPEKTIVEN FINDER")
    print("=" * 55)
    print("Finde und teste geografisch überlappende öffentliche Webcams!")
    
    finder = OverlappingCameraFinder()
    
    # Finde überlappende Paare
    overlapping_pairs = finder.find_overlapping_pairs(max_distance_km=3.0)
    
    if len(overlapping_pairs) == 0:
        print("❌ Keine überlappenden Kamera-Paare gefunden")
        return
    
    # Zeige Top-Kandidaten
    print(f"\n🏆 TOP {min(3, len(overlapping_pairs))} ÜBERLAPPENDE PAARE:")
    for i, pair in enumerate(overlapping_pairs[:3]):
        print(f"  {i+1}. {pair['cam1']['name']} ↔ {pair['cam2']['name']}")
        print(f"     📏 {pair['distance_km']:.2f}km, 🎯 Score: {pair['overlap_score']:.2f}")
    
    # Teste bestes Paar
    if len(overlapping_pairs) > 0:
        best_pair = overlapping_pairs[0]
        print(f"\n🚀 Teste bestes Paar: {best_pair['cam1']['name']} ↔ {best_pair['cam2']['name']}")
        print("⏱️ Dauer: 5 Minuten synchroner Test")
        print("🛑 Drücken Sie Ctrl+C zum Stoppen")
        
        try:
            session_dir, results, analysis = finder.test_overlapping_pair(best_pair, duration_minutes=5)
            
            print("\n🎉 Überlappungstest abgeschlossen!")
            print(f"📁 Session: {session_dir}")
            
            if analysis['overlap_quality'] == 'high':
                print("✅ HOHE ÜBERLAPPUNG erkannt - perfekt für 3D-Tracking!")
            elif analysis['overlap_quality'] == 'medium':
                print("🟡 MITTLERE ÜBERLAPPUNG - gut für Vergleichstests")
            else:
                print("🔴 NIEDRIGE ÜBERLAPPUNG - aber dennoch wertvoll für Tests")
                
        except KeyboardInterrupt:
            print("\n🛑 Test gestoppt")
        except Exception as e:
            print(f"\n❌ Test-Fehler: {e}")

if __name__ == "__main__":
    main()
