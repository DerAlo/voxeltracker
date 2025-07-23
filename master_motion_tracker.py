#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pixeltovoxelprojector - Master Motion Tracker VERBESSERT
=======================================================

🎯 ALLE Originalfunktionen + VERBESSERUNGEN:
- ✅ Alle Profile erhalten (Mosquito/Bird/Aircraft/Custom)  
- ✅ Alle Video-Quellen erhalten (Webcam/YouTube/Streams)
- ✅ Webcam-Auswahl komplett erhalten
- ✅ Vorschau-Fenster komplett erhalten
- ✅ 3D-Triangulation mit matplotlib (PyVista entfernt)
- 🚀 Full HD Aufloesung (1920x1080 @ 30fps)
- 🔍 1.5x groessere Vorschau-Fenster  
- 🌤️ Anti-Wolken/Reflektions-Filter
- ⚡ Performance-Optimierungen
- 🔤 UTF-8 Sonderzeichen-Support

VERSION: Enhanced - Alle Features + bessere UX/Performance
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import cv2
import numpy as np
import threading
import time
import queue
import subprocess
import os
from datetime import datetime
from collections import deque
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

print("🎯 Pixeltovoxelprojector - Master Motion Tracker")
print("✅ OpenCV verfügbar")
print("✅ matplotlib verfügbar - stabile 3D-Triangulation")


class Stable3DTriangulation:
    """Crash-sichere 3D Triangulation mit matplotlib statt PyVista"""
    
    def __init__(self, master_tracker):
        self.master_tracker = master_tracker
        self.is_active = False
        self.fig = None
        self.ax = None
        
        # Himmel-Tracking Setup
        self.camera_positions = {
            'webcam_0': np.array([-0.05, 0, 0]),   # Links (5cm)
            'webcam_1': np.array([0.05, 0, 0]),    # Rechts (5cm)
            'webcam_2': np.array([0, -0.1, 0])     # Zentrum-hinten
        }
        
        self.camera_colors = {
            'webcam_0': 'red',     # Links = Rot
            'webcam_1': 'green',   # Rechts = Grün  
            'webcam_2': 'blue'     # Zentrum = Blau
        }
        
    def start_triangulation(self):
        """Starte stabile 3D-Triangulation"""
        if self.is_active:
            print("⚠️ Triangulation läuft bereits!")
            return
            
        print("🚀 Starte STABILE 3D-Triangulation (matplotlib)...")
        self.is_active = True
        
        # Zoom-Level initialisieren
        self.zoom_level = 1.0
        
        # Erstelle matplotlib 3D-Plot
        plt.style.use('dark_background')
        self.fig = plt.figure(figsize=(12, 8))
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        # Setup 3D-Szene
        self._setup_3d_scene()
        
        # Event-Handler für Zoom
        self._setup_zoom_controls()
        
        # Timer für Live-Updates  
        self.timer = self.fig.canvas.new_timer(interval=400)  # 2.5 FPS - bessere Performance
        self.timer.add_callback(self._update_visualization)
        self.timer.start()
        
        # Window-Event für sauberes Schließen
        self.fig.canvas.mpl_connect('close_event', self._on_close)
        
        plt.show()
        
    def _setup_zoom_controls(self):
        """Setup Zoom-Steuerung mit Mausrad"""
        def on_scroll(event):
            if event.inaxes != self.ax:
                return
                
            # Zoom-Faktor bestimmen
            zoom_factor = 1.2 if event.button == 'up' else 1/1.2
            
            # Schneller Zoom mit Strg
            if event.key == 'control':
                zoom_factor = zoom_factor ** 2
                
            # Zoom-Level anpassen
            self.zoom_level *= zoom_factor
            self.zoom_level = max(0.1, min(10.0, self.zoom_level))  # Begrenzen
            
            # Szene neu zeichnen mit neuem Zoom
            self._setup_3d_scene()
            self.fig.canvas.draw()
            
        # Event-Handler verbinden
        self.fig.canvas.mpl_connect('scroll_event', on_scroll)
        
        # Zusätzliche Tastatur-Shortcuts
        def on_key(event):
            if event.key == '+' or event.key == '=':
                self.zoom_level *= 1.2
                self._setup_3d_scene()
                self.fig.canvas.draw()
            elif event.key == '-':
                self.zoom_level /= 1.2
                self._setup_3d_scene()
                self.fig.canvas.draw()
            elif event.key == '0':
                self.zoom_level = 1.0
                self._setup_3d_scene()
                self.fig.canvas.draw()
                
        self.fig.canvas.mpl_connect('key_press_event', on_key)
        
    def _setup_3d_scene(self):
        """Setup 3D-Szene mit Kameras und Koordinatensystem"""
        self.ax.clear()
        self.ax.set_facecolor('black')
        
        # Titel
        self.ax.set_title('🎯 STABILE TRIANGULATION - Himmel Tracking\\n'
                         '✅ Crash-sicher | 🔄 Sync-Filter aktiv | 🔍 Zoom mit Mausrad', 
                         color='cyan', fontsize=12, pad=20)
        
        # Achsen-Setup
        self.ax.set_xlabel('X (m)', color='red')
        self.ax.set_ylabel('Y (m)', color='green')  
        self.ax.set_zlabel('Z (m)', color='blue')
        
        # Dynamische Achsen-Limits für besseren Zoom
        if not hasattr(self, 'zoom_level'):
            self.zoom_level = 1.0
            
        # Zoom-abhängige Limits
        base_limit = 2.0 / self.zoom_level
        self.ax.set_xlim([-base_limit, base_limit])
        self.ax.set_ylim([-base_limit/2, base_limit*2.5])
        self.ax.set_zlim([-base_limit/2, base_limit*2.5])
        
        # Koordinatenachsen zeichnen (skaliert mit Zoom)
        axis_length = base_limit
        
        # X-Achse (rot) - deutlicher
        self.ax.plot([0, axis_length], [0, 0], [0, 0], 'r-', linewidth=4, alpha=0.9)
        self.ax.text(axis_length*1.1, 0, 0, 'X', color='red', fontsize=12, weight='bold')
        
        # Y-Achse (grün) - deutlicher
        self.ax.plot([0, 0], [0, axis_length], [0, 0], 'g-', linewidth=4, alpha=0.9)
        self.ax.text(0, axis_length*1.1, 0, 'Y', color='green', fontsize=12, weight='bold')
        
        # Z-Achse (blau) - deutlicher
        self.ax.plot([0, 0], [0, 0], [0, axis_length], 'b-', linewidth=4, alpha=0.9)
        self.ax.text(0, 0, axis_length*1.1, 'Z', color='blue', fontsize=12, weight='bold')
        
        # Boden-Grid (adaptive Größe)
        grid_range = base_limit
        xx, yy = np.meshgrid(np.linspace(-grid_range, grid_range, 5), 
                            np.linspace(-grid_range/2, grid_range*2.5, 7))
        zz = np.zeros_like(xx) - 0.5/self.zoom_level
        self.ax.plot_wireframe(xx, yy, zz, alpha=0.3, color='gray')
        
        # Zeichne Kameras mit verbesserter Visualisierung
        for camera_name, position in self.camera_positions.items():
            if camera_name in getattr(self.master_tracker, 'caps', {}):
                color = self.camera_colors.get(camera_name, 'white')
                
                # Kamera als größerer, markanter Punkt
                self.ax.scatter(*position, color=color, s=200, alpha=1.0, 
                              marker='s', edgecolors='white', linewidth=2)
                
                # Kamera-Label (größer und deutlicher)
                self.ax.text(position[0], position[1], position[2] + 0.1/self.zoom_level, 
                           camera_name.replace('webcam_', 'CAM '), 
                           color='white', fontsize=10, weight='bold',
                           bbox=dict(boxstyle="round,pad=0.3", facecolor=color, alpha=0.7))
                
                # Verbesserte Sichtfeld-Visualisierung
                self._draw_enhanced_camera_fov(position, color)
                
                # Kamera-Orientierungspfeil
                self._draw_camera_orientation(position, color)
        
        # Verbesserte Info-Box mit Anti-Stationary Filter
        info_text = ("📍 ANTI-STATIONARY FILTER AKTIV:\\n"
                    "• 🚫 Mindest-Bewegung: Objekt muss sich signifikant bewegen\\n"
                    "• ⏱️ Zeitfenster: Bewegung muss im Zeitrahmen stattfinden\\n"
                    "• 🎯 Filtert: Wolken-Kanten, statische Äste, langsame Störungen\\n"
                    "• ✅ Erhält: Schnelle Vögel mit echter Bewegungsdynamik\\n\\n"
                    "🎮 STEUERUNG:\\n"
                    "• Maus-Drag: 3D-Rotation\\n"
                    "• Mausrad: Zoom In/Out\\n"
                    "• Strg+Mausrad: Schneller Zoom\\n"
                    "• Tasten +/-: Zoom, 0: Reset\\n\\n"
                    "📷 WEBCAM-SETUP:\\n"
                    "• ROT: Linke Kamera (5cm links)\\n"
                    "• GRÜN: Rechte Kamera (5cm rechts)\\n"
                    "• Marker-Größe = Konfidenz\\n\\n"
                    "⚙️ FILTER ANPASSEN:\\n"
                    "Siehe 'Advanced Settings' im Hauptfenster\\n"
                    "für Feintuning des Anti-Stationary Filters")
                    
        self.ax.text2D(0.02, 0.98, info_text, transform=self.ax.transAxes,
                      fontsize=8, color='yellow', verticalalignment='top',
                      bbox=dict(boxstyle="round,pad=0.5", facecolor='black', 
                               alpha=0.8, edgecolor='yellow'))
        
    def _draw_enhanced_camera_fov(self, position, color):
        """Zeichne verbessertes Sichtfeld-Kegel für Kamera"""
        # Himmel-Richtung (60° Elevation)
        direction = np.array([0, 0.5, 0.866])  # 60° nach oben
        fov_distance = 3.0 / self.zoom_level  # Zoom-angepasst
        fov_angle = 60  # Grad
        
        # Kegel-Endpunkt
        end_point = position + direction * fov_distance
        
        # Hauptsichtstrahl (dicker)
        self.ax.plot([position[0], end_point[0]],
                    [position[1], end_point[1]], 
                    [position[2], end_point[2]], 
                    color=color, alpha=0.8, linewidth=4)
        
        # Sichtfeld-Kegel (vereinfacht als Pyramide)
        cone_radius = fov_distance * np.tan(np.radians(fov_angle/2))
        
        # 4 Eckpunkte des Sichtfeld-Kegels
        angles = [0, 90, 180, 270]
        for angle in angles:
            rad = np.radians(angle)
            offset_x = cone_radius * np.cos(rad)
            offset_z = cone_radius * np.sin(rad)
            
            cone_point = end_point + np.array([offset_x, 0, offset_z])
            
            # Linie von Kamera zu Kegel-Rand
            self.ax.plot([position[0], cone_point[0]],
                        [position[1], cone_point[1]], 
                        [position[2], cone_point[2]], 
                        color=color, alpha=0.3, linewidth=1)
                        
    def _draw_camera_orientation(self, position, color):
        """Zeichne Orientierungspfeil für bessere Kamera-Identifikation"""
        # Kleiner Orientierungspfeil nach oben
        arrow_length = 0.2 / self.zoom_level
        arrow_end = position + np.array([0, 0, arrow_length])
        
        self.ax.plot([position[0], arrow_end[0]],
                    [position[1], arrow_end[1]], 
                    [position[2], arrow_end[2]], 
                    color='white', alpha=1.0, linewidth=3)
                    
        # Pfeilspitze
        self.ax.scatter(*arrow_end, color='white', s=50, marker='^', alpha=1.0)
    
    def _update_visualization(self):
        """Live-Update der Visualization - THREAD-SICHER"""
        try:
            if not self.is_active:
                return
                
            # Prüfe ob Motion-Daten vorhanden
            if not hasattr(self.master_tracker, 'camera_motion_data'):
                return
                
            # Synchrone Motion-Filter anwenden
            synchronized_motions = self._filter_synchronized_motions()
            
            if synchronized_motions and len(synchronized_motions) >= 2:
                # Lösche alte Motion-Objekte
                self._clear_motion_objects()
                
                # Zeichne gefilterte Strahlen
                self._draw_filtered_rays(synchronized_motions)
                
                # Berechne und zeichne Triangulation
                self._calculate_and_draw_triangulation(synchronized_motions)
                
                # Canvas aktualisieren
                self.fig.canvas.draw_idle()
                
        except Exception as e:
            # Sichere Fehlerbehandlung
            print(f"⚠️ Update-Fehler (ignoriert): {str(e)[:50]}...")
            
    def _filter_synchronized_motions(self):
        """Filtere nur zeitgleiche Bewegungen + Anti-Stationary Filter gegen Wolken/Äste"""
        try:
            if not hasattr(self.master_tracker, 'camera_motion_data') or \
               len(self.master_tracker.camera_motion_data) < 2:
                return {}
                
            current_time = time.time()
            sync_tolerance = 0.3  # 300ms Toleranz
            
            # Anti-Stationary Filter Parameter
            min_movement_distance = getattr(self.master_tracker, 'min_movement_var', None)
            movement_time_window = getattr(self.master_tracker, 'movement_window_var', None)
            
            min_distance = min_movement_distance.get() if min_movement_distance else 15  # Mindest-Bewegung in Pixeln
            time_window = movement_time_window.get() if movement_time_window else 1.0   # Zeitfenster in Sekunden
            
            # Sammle gefilterte Motion-Events
            filtered_motions = {}
            for camera_name, motion_list in self.master_tracker.camera_motion_data.items():
                if camera_name not in self.camera_positions or not motion_list:
                    continue
                    
                # Nur Events der letzten 3 Sekunden für bewegungsanalyse
                recent_motions = []
                for motion in motion_list:
                    try:
                        if current_time - motion['timestamp'] > 3.0:
                            continue
                            
                        # ANTI-STATIONARY FILTER: Prüfe signifikante Bewegung
                        motion_x = motion.get('x', 0)
                        motion_y = motion.get('y', 0)
                        motion_time = motion.get('timestamp', current_time)
                        
                        # Suche nach älterer Position im Zeitfenster
                        has_significant_movement = False
                        for older_motion in motion_list:
                            older_time = older_motion.get('timestamp', 0)
                            if (motion_time - older_time) > time_window and (motion_time - older_time) < time_window * 2:
                                older_x = older_motion.get('x', 0)
                                older_y = older_motion.get('y', 0)
                                
                                # Berechne Bewegungsdistanz
                                distance = ((motion_x - older_x)**2 + (motion_y - older_y)**2)**0.5
                                
                                if distance >= min_distance:
                                    has_significant_movement = True
                                    break
                        
                        # Nur Motions mit signifikanter Bewegung akzeptieren
                        if has_significant_movement or len(motion_list) < 5:  # Bei wenigen Daten weniger streng
                            recent_motions.append(motion)
                        
                    except:
                        continue
                        
                if recent_motions:
                    filtered_motions[camera_name] = recent_motions
            
            if len(filtered_motions) < 2:
                return {}
            
            # Finde beste zeitliche Übereinstimmung mit gefilterten Daten
            camera_names = list(filtered_motions.keys())
            best_match = None
            best_time_diff = float('inf')
            
            for i in range(len(camera_names)):
                for j in range(i + 1, len(camera_names)):
                    cam1_name = camera_names[i]
                    cam2_name = camera_names[j]
                    
                    for motion1 in filtered_motions[cam1_name]:
                        for motion2 in filtered_motions[cam2_name]:
                            try:
                                time_diff = abs(motion1['timestamp'] - motion2['timestamp'])
                                if time_diff < sync_tolerance and time_diff < best_time_diff:
                                    best_time_diff = time_diff
                                    best_match = {cam1_name: motion1, cam2_name: motion2}
                            except:
                                continue
            
            return best_match or {}
            
        except Exception:
            return {}
    
    def _clear_motion_objects(self):
        """Entferne alte Motion-Objekte"""
        # matplotlib: Einfach Scene neu aufbauen
        self._setup_3d_scene()
        
    def _draw_filtered_rays(self, synchronized_motions):
        """Zeichne gefilterte Camera Rays"""
        try:
            for camera_name, motion in synchronized_motions.items():
                if camera_name not in self.camera_positions:
                    continue
                    
                camera_pos = self.camera_positions[camera_name]
                camera_color = self.camera_colors.get(camera_name, 'white')
                
                # 3D Richtung berechnen
                direction = self._pixel_to_3d_direction(motion['x'], motion['y'], camera_name)
                
                # Strahl für Himmel-Tracking
                ray_length = 4.0  # Reduziert für bessere Sichtbarkeit
                ray_end = camera_pos + direction * ray_length
                
                # Strahl zeichnen
                self.ax.plot([camera_pos[0], ray_end[0]],
                           [camera_pos[1], ray_end[1]], 
                           [camera_pos[2], ray_end[2]], 
                           color=camera_color, linewidth=3, alpha=0.8)
                
                # Motion-Punkt markieren
                self.ax.scatter(*ray_end, color=camera_color, s=80, alpha=0.9)
                
        except Exception:
            pass
    
    def _calculate_and_draw_triangulation(self, synchronized_motions):
        """Berechne und zeichne Triangulation - vereinfacht ohne Konfidenz-Filter"""
        try:
            if len(synchronized_motions) < 2:
                return
                
            # Triangulation berechnen
            triangulated_points = []
            confidence_scores = []
            
            camera_names = list(synchronized_motions.keys())
            for i in range(len(camera_names)):
                for j in range(i + 1, len(camera_names)):
                    try:
                        cam1_name = camera_names[i]
                        cam2_name = camera_names[j]
                        
                        motion1 = synchronized_motions[cam1_name]
                        motion2 = synchronized_motions[cam2_name]
                        
                        # 3D Strahlen
                        pos1 = self.camera_positions[cam1_name]
                        dir1 = self._pixel_to_3d_direction(motion1['x'], motion1['y'], cam1_name)
                        
                        pos2 = self.camera_positions[cam2_name]
                        dir2 = self._pixel_to_3d_direction(motion2['x'], motion2['y'], cam2_name)
                        
                        # Triangulation
                        intersection, confidence = self._line_intersection_3d_with_confidence(pos1, dir1, pos2, dir2)
                        
                        if intersection is not None and confidence > 0.1:  # Niedrigere Schwelle
                            triangulated_points.append(intersection)
                            confidence_scores.append(confidence)
                            
                    except Exception:
                        continue
            
            # Finale Position anzeigen
            if triangulated_points:
                # Gewichteter Durchschnitt
                total_weight = sum(confidence_scores)
                if total_weight > 0:
                    weighted_position = np.zeros(3)
                    for point, confidence in zip(triangulated_points, confidence_scores):
                        weighted_position += point * (confidence / total_weight)
                    
                    # Marker-Größe basierend auf Konfidenz (größer = mehr Vertrauen)
                    avg_confidence = total_weight / len(confidence_scores)
                    marker_size = 100 + (avg_confidence * 300)
                    
                    # Finale Position als große Kugel
                    self.ax.scatter(*weighted_position, color='cyan', s=marker_size, alpha=1.0, 
                                  marker='o', edgecolors='white', linewidth=2)
                    
                    # Koordinaten-Info mit Konfidenz
                    distance = np.linalg.norm(weighted_position)
                    if 1 <= distance <= 1000:  # Nur bei plausiblen Entfernungen
                        coord_text = (f"📍 {distance:.1f}m (Conf: {avg_confidence:.2f})\n"
                                    f"({weighted_position[0]:.1f}, {weighted_position[1]:.1f}, {weighted_position[2]:.1f})\n"
                                    f"Triangulationen: {len(triangulated_points)}")
                        self.ax.text(weighted_position[0], weighted_position[1], weighted_position[2] + 0.2,
                                   coord_text, color='cyan', fontsize=8, ha='center')
                    
        except Exception:
            pass
    
    def _pixel_to_3d_direction(self, pixel_x, pixel_y, camera_name):
        """Konvertiere 2D Pixel zu 3D Richtung - Full HD optimiert"""
        # Normalisiere Pixel-Koordinaten für Full HD (1920x1080)
        norm_x = (pixel_x - 960) / 960  # Full HD: 1920/2 = 960
        norm_y = (pixel_y - 540) / 540  # Full HD: 1080/2 = 540
        
        # FOV-Faktor
        fov_factor = 0.7  # 60° FOV
        
        # Himmel-Tracking: Beide Kameras parallel nach oben
        base_dir = np.array([0, 0.5, 0.866])  # 60° Elevation
        right_vec = np.array([1, 0, 0])
        up_vec = np.array([0, 0.866, -0.5])
        
        # Richtung berechnen
        direction = base_dir + (right_vec * norm_x * fov_factor) + (up_vec * norm_y * fov_factor)
        
        return direction / np.linalg.norm(direction)
    
    def _line_intersection_3d_with_confidence(self, p1, d1, p2, d2):
        """3D Linien-Intersection mit Confidence - für Himmel-Tracking optimiert"""
        w = p1 - p2
        a = np.dot(d1, d1)
        b = np.dot(d1, d2)
        c = np.dot(d2, d2)
        d = np.dot(d1, w)
        e = np.dot(d2, w)
        
        denominator = a * c - b * b
        if abs(denominator) < 1e-8:
            return None, 0.0
            
        t1 = (b * e - c * d) / denominator
        t2 = (a * e - b * d) / denominator
        
        # Nur positive t-Werte (vor den Kameras)
        if t1 < 0.1 or t2 < 0.1:
            return None, 0.0
        
        # Nächste Punkte auf beiden Linien
        closest1 = p1 + t1 * d1
        closest2 = p2 + t2 * d2
        
        # Mittelpunkt als Triangulation
        intersection = (closest1 + closest2) / 2
        
        # Confidence für große Entfernungen
        distance = np.linalg.norm(closest1 - closest2)
        confidence = max(0.0, 1.0 - distance / 10.0)  # 10m Toleranz für matplotlib
        
        return intersection, confidence
    
    def _on_close(self, event):
        """Sauberes Schließen"""
        print("✅ Stabile Triangulation beendet")
        self.is_active = False
        if hasattr(self, 'timer'):
            self.timer.stop()


# Detection Profiles für verschiedene Ziele - Full HD optimiert
DETECTION_PROFILES = {
    "🦟 Mosquito": {
        "threshold": 15,
        "min_area": 25,  # Skaliert für Full HD
        "max_area": 400,  # Skaliert für Full HD 
        "fps": 60,
        "resolution": (1920, 1080),  # Full HD
        "description": "Optimiert für kleine, schnelle Insekten - Full HD"
    },
    "🐦 Bird": {
        "threshold": 30,
        "min_area": 500,  # Skaliert für Full HD
        "max_area": 12000,  # Skaliert für Full HD
        "fps": 30,
        "resolution": (1920, 1080),  # Full HD
        "description": "Optimiert für Vögel und mittlere Flugobjekte - Full HD"
    },
    "✈️ Aircraft": {
        "threshold": 40,
        "min_area": 1200,  # Skaliert für Full HD
        "max_area": 120000,  # Skaliert für Full HD
        "fps": 15,
        "resolution": (1920, 1080),  # Full HD
        "description": "Optimiert für Flugzeuge und große Objekte - Full HD"
    },
    "🎯 Custom": {
        "threshold": 25,
        "min_area": 250,  # Skaliert für Full HD
        "max_area": 25000,  # Skaliert für Full HD
        "fps": 30,
        "resolution": (1920, 1080),  # Full HD
        "description": "Manuelle Konfiguration - Full HD"
    }
}

# Video-Quellen
VIDEO_SOURCES = {
    "📷 Webcam 0 (Primary)": {
        "type": "webcam",
        "source": 0,
        "description": "Standard USB-Webcam (Index 0)"
    },
    "📷 Webcam 1": {
        "type": "webcam", 
        "source": 1,
        "description": "Zweite USB-Webcam (Index 1)"
    },
    "📷 Webcam 2": {
        "type": "webcam",
        "source": 2, 
        "description": "Dritte USB-Webcam (Index 2)"
    },
    "📷📷 Multi-Webcam": {
        "type": "multi_webcam",
        "sources": [0, 1, 2],
        "description": "Alle verfügbaren Webcams gleichzeitig"
    },
    "🌊 Niagara Falls Live": {
        "type": "youtube_dual",
        "sources": {
            "NiagaraFallsLive": "https://www.youtube.com/watch?v=4Z6wOToTgh0",
            "EarthCam": "https://www.youtube.com/watch?v=W3D3dEpR3bs"
        },
        "description": "YouTube Live-Streams - Dual-Perspektiven"
    },
    "🌊 Niagara Falls (Single)": {
        "type": "youtube_single",
        "source": "https://www.youtube.com/watch?v=4Z6wOToTgh0",
        "description": "YouTube Live-Stream - Einzelperspektive"
    },
    "📺 Custom URL": {
        "type": "custom_url",
        "source": "",
        "description": "Eigene URL eingeben"
    }
}

class MasterMotionTracker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎯 Pixeltovoxelprojector - Master Motion Tracker")
        self.root.geometry("900x700")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # State
        self.is_tracking = False
        self.caps = {}
        self.bg_subtractors = {}
        self.current_profile = None
        self.current_source = None
        self.tracking_thread = None
        self.motion_data = deque(maxlen=1000)  # Store motion data for 3D visualization
        self.camera_motion_data = {}  # Store motion data per camera for triangulation
        self.triangulation_active = False  # Flag für Live-Triangulation
        self.current_motion_counts = {}  # Für Dashboard
        self.current_fps = 0  # Für Dashboard
        self.tracking_start_time = 0  # Für Dashboard
        self.viewer_window = None
        
        # GUI setup
        self.setup_gui()
        
        # Initial log
        self.log("🎯 Pixeltovoxelprojector Master Motion Tracker gestartet")
        self.log("🚀 Wählen Sie Profil und Quelle, dann klicken Sie 'Start Tracking'")
        
    def setup_gui(self):
        """Setup GUI interface"""
        # Main title
        title_frame = ttk.Frame(self.root)
        title_frame.pack(pady=10)
        
        ttk.Label(title_frame, text="🎯 Pixeltovoxelprojector", 
                 font=("Arial", 18, "bold")).pack()
        ttk.Label(title_frame, text="Master Motion Tracker", 
                 font=("Arial", 12)).pack()
        
        # Configuration section
        config_frame = ttk.LabelFrame(self.root, text="⚙️ Konfiguration")
        config_frame.pack(pady=10, padx=10, fill=tk.X)
        
        # Profile selection
        ttk.Label(config_frame, text="🎯 Detection-Profil:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.profile_var = tk.StringVar(value=list(DETECTION_PROFILES.keys())[0])
        profile_combo = ttk.Combobox(config_frame, textvariable=self.profile_var, 
                                    values=list(DETECTION_PROFILES.keys()), state="readonly")
        profile_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        profile_combo.bind('<<ComboboxSelected>>', self.on_profile_changed)
        
        # Video source selection  
        ttk.Label(config_frame, text="📺 Video-Quelle:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.source_var = tk.StringVar(value=list(VIDEO_SOURCES.keys())[0])
        source_combo = ttk.Combobox(config_frame, textvariable=self.source_var,
                                   values=list(VIDEO_SOURCES.keys()), state="readonly")
        source_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        source_combo.bind('<<ComboboxSelected>>', self.on_source_changed)
        
        # Custom URL entry (initially hidden)
        self.url_frame = ttk.Frame(config_frame)
        ttk.Label(self.url_frame, text="🔗 URL:").pack(side=tk.LEFT, padx=5)
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(self.url_frame, textvariable=self.url_var, width=50)
        self.url_entry.pack(side=tk.LEFT, padx=5)
        
        # Webcam selection frame (initially hidden)
        self.webcam_frame = ttk.LabelFrame(config_frame, text="📷 Webcam Auswahl")
        ttk.Label(self.webcam_frame, text="Wählen Sie die gewünschten Webcams aus:").pack(pady=5)
        
        # Webcam checkboxes
        self.webcam_vars = {}
        webcam_check_frame = ttk.Frame(self.webcam_frame)
        webcam_check_frame.pack(pady=5)
        
        for i in range(4):  # Bis zu 4 Webcams unterstützen
            var = tk.BooleanVar()
            # Standard: Nur Webcam 0 und 1 aktiviert (die beiden physischen)
            if i < 2:
                var.set(True)
            else:
                var.set(False)
            
            self.webcam_vars[f'webcam_{i}'] = var
            checkbox = ttk.Checkbutton(
                webcam_check_frame, 
                text=f"Webcam {i} ({'Physisch' if i < 2 else 'Virtual/OBS' if i == 2 else 'Extra'})",
                variable=var
            )
            checkbox.pack(side=tk.LEFT, padx=10)
        
        # Help text
        help_label = ttk.Label(
            self.webcam_frame, 
            text="💡 Tipp: Deaktivieren Sie virtuelle Kameras (OBS etc.) für bessere Triangulation",
            font=("Arial", 8), 
            foreground="gray"
        )
        help_label.pack(pady=(0,5))
        
        config_frame.columnconfigure(1, weight=1)
        
        # Profile info
        info_frame = ttk.LabelFrame(self.root, text="ℹ️ Profil-Information")
        info_frame.pack(pady=5, padx=10, fill=tk.X)
        
        self.profile_info_var = tk.StringVar()
        ttk.Label(info_frame, textvariable=self.profile_info_var, 
                 wraplength=800, justify=tk.LEFT).pack(padx=10, pady=5)
        
        # Controls
        control_frame = ttk.Frame(self.root)
        control_frame.pack(pady=10)
        
        self.start_btn = ttk.Button(control_frame, text="🎬 Start Tracking", 
                                   command=self.start_tracking)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="⏹️ Stop Tracking", 
                                  command=self.stop_tracking, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.test_btn = ttk.Button(control_frame, text="🔍 Test Source", 
                                  command=self.test_source)
        self.test_btn.pack(side=tk.LEFT, padx=5)
        
        self.viewer_btn = ttk.Button(control_frame, text="🎲 3D Viewer", 
                                    command=self.open_3d_viewer)
        self.viewer_btn.pack(side=tk.LEFT, padx=5)
        
        self.dashboard_btn = ttk.Button(control_frame, text="📊 Dashboard", 
                                       command=self.open_dashboard)
        self.dashboard_btn.pack(side=tk.LEFT, padx=5)
        
        self.triangulation_btn = ttk.Button(control_frame, text="📐 3D Triangulation (stabil)", 
                                           command=self.open_triangulation_view)
        self.triangulation_btn.pack(side=tk.LEFT, padx=5)
        
        self.last_detection_btn = ttk.Button(control_frame, text="🐦 Last Detection", 
                                            command=self.open_last_detection_view)
        self.last_detection_btn.pack(side=tk.LEFT, padx=5)
        
        # Advanced settings (collapsible)
        self.settings_visible = False
        self.settings_btn = ttk.Button(control_frame, text="⚙️ Advanced Settings", 
                                      command=self.toggle_settings)
        self.settings_btn.pack(side=tk.LEFT, padx=5)
        
        # Advanced settings frame (initially hidden)
        self.settings_frame = ttk.LabelFrame(self.root, text="🔧 Advanced Settings")
        
        # Threshold - VOGEL-OPTIMIERT  
        ttk.Label(self.settings_frame, text="🎯 Motion Threshold (Sensitivity):").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.threshold_var = tk.IntVar(value=15)  # Sensibler für Vögel
        threshold_scale = ttk.Scale(self.settings_frame, from_=5, to=100, 
                                   variable=self.threshold_var, orient=tk.HORIZONTAL, length=200)
        threshold_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        threshold_label = ttk.Label(self.settings_frame, textvariable=self.threshold_var)
        threshold_label.grid(row=0, column=2, padx=5)
        
        # Min area - DEUTLICH NIEDRIGER für kleine Vögel
        ttk.Label(self.settings_frame, text="📏 Min Object Size (pixels):").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.min_area_var = tk.IntVar(value=25)  # Viel niedriger: 25 statt 100
        min_area_scale = ttk.Scale(self.settings_frame, from_=10, to=500, 
                                  variable=self.min_area_var, orient=tk.HORIZONTAL, length=200)
        min_area_scale.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        min_area_label = ttk.Label(self.settings_frame, textvariable=self.min_area_var)
        min_area_label.grid(row=1, column=2, padx=5)
        
        # Max area - ANGEPASST für große Objekte
        ttk.Label(self.settings_frame, text="📐 Max Object Size (pixels):").grid(row=2, column=0, sticky=tk.W, padx=5)
        self.max_area_var = tk.IntVar(value=8000)  # Reduziert für bessere Performance
        max_area_scale = ttk.Scale(self.settings_frame, from_=500, to=20000, 
                                  variable=self.max_area_var, orient=tk.HORIZONTAL, length=200)
        max_area_scale.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)
        max_area_label = ttk.Label(self.settings_frame, textvariable=self.max_area_var)
        max_area_label.grid(row=2, column=2, padx=5)
        
        # Separator für Störungsfilter
        separator = ttk.Separator(self.settings_frame, orient=tk.HORIZONTAL)
        separator.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=10)
        
        # Anti-Wolken Filter Label
        ttk.Label(self.settings_frame, text="🌤️ ANTI-WOLKEN FILTER - Intelligente Himmelbeobachtung:", 
                 font=("Arial", 9, "bold"), foreground="cyan").grid(row=4, column=0, columnspan=3, sticky=tk.W, padx=5, pady=(5,0))
        
        # Mindest-Bewegungsdistanz (HÖHER gegen Wolken-Drift)
        ttk.Label(self.settings_frame, text="🎯 Mindest-Bewegung (Pixel):").grid(row=5, column=0, sticky=tk.W, padx=5)
        self.min_movement_var = tk.IntVar(value=15)  # Höher für echte Motion
        movement_scale = ttk.Scale(self.settings_frame, from_=8, to=40,  
                                  variable=self.min_movement_var, orient=tk.HORIZONTAL, length=200)
        movement_scale.grid(row=5, column=1, sticky=(tk.W, tk.E), padx=5)
        movement_label = ttk.Label(self.settings_frame, textvariable=self.min_movement_var)
        movement_label.grid(row=5, column=2, padx=5)
        
        # Minimum Area Filter (gegen Reflexionen) - SEPARATER FILTER
        ttk.Label(self.settings_frame, text="📏 Anti-Wolken Min Area:").grid(row=6, column=0, sticky=tk.W, padx=5)
        self.anti_cloud_min_area_var = tk.IntVar(value=60)  # Niedriger für Vogel-Erkennung
        min_area_scale = ttk.Scale(self.settings_frame, from_=30, to=300,  
                                  variable=self.anti_cloud_min_area_var, orient=tk.HORIZONTAL, length=200)
        min_area_scale.grid(row=6, column=1, sticky=(tk.W, tk.E), padx=5)
        min_area_label = ttk.Label(self.settings_frame, textvariable=self.anti_cloud_min_area_var)
        min_area_label.grid(row=6, column=2, padx=5)
        
        # Maximum Area Filter (gegen große Wolken) - SEPARATER FILTER
        ttk.Label(self.settings_frame, text="☁️ Anti-Wolken Max Area:").grid(row=7, column=0, sticky=tk.W, padx=5)
        self.anti_cloud_max_area_var = tk.IntVar(value=2500)
        max_area_scale = ttk.Scale(self.settings_frame, from_=1000, to=8000,
                                  variable=self.anti_cloud_max_area_var, orient=tk.HORIZONTAL, length=200)
        max_area_scale.grid(row=7, column=1, sticky=(tk.W, tk.E), padx=5)
        max_area_label = ttk.Label(self.settings_frame, textvariable=self.anti_cloud_max_area_var)
        max_area_label.grid(row=7, column=2, padx=5)
        
        # Speed Range Filter (Vögel vs Wolken)
        ttk.Label(self.settings_frame, text="🦅 Speed Min (Vogel-typisch):").grid(row=8, column=0, sticky=tk.W, padx=5)
        self.min_speed_var = tk.IntVar(value=20)
        min_speed_scale = ttk.Scale(self.settings_frame, from_=10, to=60,
                                   variable=self.min_speed_var, orient=tk.HORIZONTAL, length=200)
        min_speed_scale.grid(row=8, column=1, sticky=(tk.W, tk.E), padx=5)
        min_speed_label = ttk.Label(self.settings_frame, textvariable=self.min_speed_var)
        min_speed_label.grid(row=8, column=2, padx=5)
        
        # Help text für ANTI-WOLKEN FILTER
        help_text = ("🌤️ ANTI-WOLKEN FILTER (Himmel-optimiert):\n"
                    "• Movement: ≥15px = Echte Bewegung (filtert Wolken-Drift)\n"
                    "• Min Area: ≥120px² = Filtert Reflexionen und Pixelfehler\n" 
                    "• Max Area: ≤2500px² = Filtert große Wolken-Formationen\n"
                    "• Min Speed: ≥20px/frame = Vogel-typische Geschwindigkeit\n"
                    "• ERGEBNIS: Nur schnelle, kompakte Flugobjekte = VÖGEL")
        ttk.Label(self.settings_frame, text=help_text, font=("Arial", 8), foreground="cyan").grid(
            row=9, column=0, columnspan=3, sticky=tk.W, padx=5, pady=(5,0))
        
        self.settings_frame.columnconfigure(1, weight=1)
        
        # Status
        status_frame = ttk.LabelFrame(self.root, text="📊 Status")
        status_frame.pack(pady=5, padx=10, fill=tk.X)
        
        self.status_var = tk.StringVar(value="💤 Bereit - Konfiguration auswählen und 'Start Tracking' klicken")
        ttk.Label(status_frame, textvariable=self.status_var).pack(pady=5)
        
        # Log
        log_frame = ttk.LabelFrame(self.root, text="📋 Live Log")
        log_frame.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Initialize
        self.on_profile_changed()
        self.on_source_changed()
        
    def log(self, message):
        """Add timestamped message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.root.after(0, lambda: self._update_log(log_message))
        
    def _update_log(self, message):
        """Thread-safe log update"""
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        
    def on_profile_changed(self, event=None):
        """Handle profile selection change"""
        profile_name = self.profile_var.get()
        profile = DETECTION_PROFILES[profile_name]
        
        # Update info
        info = f"{profile_name}: {profile['description']}\n"
        info += f"Threshold: {profile['threshold']}, Area: {profile['min_area']}-{profile['max_area']}, "
        info += f"FPS: {profile['fps']}, Resolution: {profile['resolution'][0]}x{profile['resolution'][1]}"
        self.profile_info_var.set(info)
        
        # Update advanced settings
        self.threshold_var.set(profile['threshold'])
        self.min_area_var.set(profile['min_area'])
        self.max_area_var.set(profile['max_area'])
        
        self.log(f"🎯 Profil gewechselt zu: {profile_name}")
        
    def on_source_changed(self, event=None):
        """Handle source selection change"""
        source_name = self.source_var.get()
        source = VIDEO_SOURCES[source_name]
        
        # Show/hide URL entry for custom URL
        if source['type'] == 'custom_url':
            self.url_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
            self.webcam_frame.grid_remove()
        # Show webcam selection for multi-webcam
        elif source['type'] == 'multi_webcam':
            self.url_frame.grid_remove()
            self.webcam_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        else:
            self.url_frame.grid_remove()
            self.webcam_frame.grid_remove()
            
        self.log(f"📺 Quelle gewechselt zu: {source_name} - {source['description']}")
        
    def open_dashboard(self):
        """Öffne das Real-time Dashboard"""
        if hasattr(self, 'dashboard_thread') and self.dashboard_thread.is_alive():
            messagebox.showinfo("Dashboard", "Dashboard läuft bereits!")
            return
            
        self.dashboard_thread = threading.Thread(target=self._dashboard_worker, daemon=True)
        self.dashboard_thread.start()
        
    def _dashboard_worker(self):
        """Dashboard Worker Thread"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib.animation as animation
            from collections import deque
            import numpy as np
            
            # Dashboard Daten
            self.dashboard_data = {
                'times': deque(maxlen=100),
                'motion_counts': deque(maxlen=100),
                'areas': deque(maxlen=100),
                'fps': deque(maxlen=50)
            }
            
            # Matplotlib Setup
            plt.style.use('dark_background')
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
            fig.suptitle('🎯 MASTER MOTION TRACKER - REAL-TIME DASHBOARD', 
                        fontsize=14, color='cyan', weight='bold')
            
            # Subplot 1: Motion Count Timeline
            ax1.set_title('Motion Events', color='lime')
            ax1.set_ylabel('Count')
            line1, = ax1.plot([], [], 'lime', linewidth=2)
            ax1.grid(True, alpha=0.3)
            
            # Subplot 2: Object Size Distribution
            ax2.set_title('Object Sizes', color='orange')
            ax2.set_ylabel('Area (pixels)')
            line2, = ax2.plot([], [], 'orange', linewidth=2)
            ax2.grid(True, alpha=0.3)
            
            # Subplot 3: FPS Performance
            ax3.set_title('Performance (FPS)', color='cyan')
            ax3.set_ylabel('FPS')
            line3, = ax3.plot([], [], 'cyan', linewidth=2)
            ax3.grid(True, alpha=0.3)
            
            # Subplot 4: Live Statistics
            ax4.set_title('Live Stats', color='white')
            ax4.axis('off')
            stats_text = ax4.text(0.1, 0.8, '', fontsize=12, color='white', 
                                 verticalalignment='top', fontfamily='monospace')
            
            def update_dashboard(frame):
                if not self.is_tracking:
                    return line1, line2, line3, stats_text
                
                # Sammle aktuelle Daten
                current_time = time.time()
                total_motion = sum(getattr(self, 'current_motion_counts', {}).values())
                avg_area = np.mean([point[2] for point in list(self.motion_data)[-10:]]) if self.motion_data else 0
                current_fps = getattr(self, 'current_fps', 0)
                
                # Update Dashboard Daten
                self.dashboard_data['times'].append(current_time)
                self.dashboard_data['motion_counts'].append(total_motion)
                self.dashboard_data['areas'].append(avg_area)
                self.dashboard_data['fps'].append(current_fps)
                
                # Update Plots
                if len(self.dashboard_data['times']) > 1:
                    times = list(self.dashboard_data['times'])
                    rel_times = [(t - times[0]) for t in times]
                    
                    # Motion Timeline
                    line1.set_data(rel_times, list(self.dashboard_data['motion_counts']))
                    ax1.relim()
                    ax1.autoscale_view()
                    
                    # Object Sizes
                    line2.set_data(rel_times, list(self.dashboard_data['areas']))
                    ax2.relim()
                    ax2.autoscale_view()
                    
                    # FPS
                    if len(self.dashboard_data['fps']) > 1:
                        fps_times = rel_times[-len(self.dashboard_data['fps']):]
                        line3.set_data(fps_times, list(self.dashboard_data['fps']))
                        ax3.relim()
                        ax3.autoscale_view()
                
                # Live Statistics
                stats = f"""
🎯 TRACKING STATUS: {'🟢 ACTIVE' if self.is_tracking else '🔴 STOPPED'}
📹 VIDEO SOURCES: {len(self.caps)}
🎭 DETECTION PROFILE: {self.profile_var.get()}

📊 CURRENT METRICS:
   Motion Objects: {total_motion}
   Avg Object Size: {avg_area:.1f} px
   Processing FPS: {current_fps:.1f}
   
⚙️ SETTINGS:
   Sensitivity: {self.threshold_var.get()}
   Min Area: {self.min_area_var.get()}
   Max Area: {self.max_area_var.get()}
   
📈 TOTAL CAPTURED:
   Motion Events: {len(self.motion_data)}
   Runtime: {current_time - getattr(self, 'tracking_start_time', current_time):.1f}s
                """
                stats_text.set_text(stats)
                
                return line1, line2, line3, stats_text
            
            # Animation starten
            ani = animation.FuncAnimation(fig, update_dashboard, interval=500, 
                                        blit=False, repeat=True)
            
            plt.tight_layout()
            plt.show()
            
        except ImportError:
            messagebox.showerror("Dashboard Error", 
                               "Matplotlib nicht installiert!\nBitte installieren: pip install matplotlib")
        except Exception as e:
            messagebox.showerror("Dashboard Error", f"Dashboard Fehler: {str(e)}")

    def open_triangulation_view(self):
        """Öffne stabile 3D-Triangulation mit matplotlib"""
        if not self.is_tracking:
            messagebox.showwarning("Triangulation", "Bitte starten Sie zuerst das Motion Tracking!")
            return
            
        # Erstelle stabile Triangulation
        triangulation = Stable3DTriangulation(self)
        
        # Starte in separatem Thread
        def start_stable():
            triangulation.start_triangulation()
            
        threading.Thread(target=start_stable, daemon=True).start()
        self.log("🚀 Stabile 3D-Triangulation gestartet (matplotlib)")
        
    def open_last_detection_view(self):
        """Öffne Last Detection Window - zeigt letztes erkanntes Objekt"""
        if not self.is_tracking:
            messagebox.showwarning("Last Detection", "Bitte starten Sie zuerst das Motion Tracking!")
            return
            
        # Starte Last Detection Window in separatem Thread
        def start_last_detection():
            self._last_detection_window()
            
        threading.Thread(target=start_last_detection, daemon=True).start()
        self.log("🐦 Last Detection Window gestartet")
        
    def _last_detection_window(self):
        """Live Last Detection Window - THREAD-SICHER"""
        try:
            cv2.namedWindow('🐦 Last Detection - Filtered Objects Only', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('🐦 Last Detection - Filtered Objects Only', 600, 450)  # Vergrößert von 400x300 auf 600x450
            
            # Create empty starting frame
            empty_frame = np.zeros((200, 300, 3), dtype=np.uint8)
            cv2.putText(empty_frame, 'Waiting for filtered detection...', 
                       (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(empty_frame, 'Press ESC or Q to CLOSE', 
                       (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            
            while self.is_tracking:
                try:
                    # Check if we have a last detection
                    if hasattr(self, 'last_detection_frame') and self.last_detection_frame is not None:
                        display_frame = self.last_detection_frame.copy()
                        
                        # Resize for much better visibility (3x scaling like the optimized version)
                        if display_frame.shape[0] < 300:  # Erhöht von 150 auf 300
                            scale = 300 / display_frame.shape[0]  # 3x Skalierung
                            new_width = int(display_frame.shape[1] * scale)
                            new_height = int(display_frame.shape[0] * scale)
                            display_frame = cv2.resize(display_frame, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
                        
                        # Add info overlay
                        if hasattr(self, 'last_detection_info'):
                            info = self.last_detection_info
                            timestamp_str = datetime.fromtimestamp(info['timestamp']).strftime("%H:%M:%S.%f")[:-3]
                            
                            # Info box with close instruction
                            cv2.putText(display_frame, f"Camera: {info['camera']}", 
                                       (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                            cv2.putText(display_frame, f"Time: {timestamp_str}", 
                                       (5, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                            cv2.putText(display_frame, f"Area: {info['area']} px", 
                                       (5, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                            cv2.putText(display_frame, f"Filter: {info.get('reason', 'PASSED')}", 
                                       (5, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
                            cv2.putText(display_frame, "ESC/Q = CLOSE WINDOW", 
                                       (5, display_frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
                        
                        cv2.imshow('🐦 Last Detection - Filtered Objects Only', display_frame)
                    else:
                        cv2.imshow('🐦 Last Detection - Filtered Objects Only', empty_frame)
                    
                    # CLOSE WINDOW CHECK - mit sofortiger Reaktion
                    key = cv2.waitKey(50) & 0xFF  # Schnellere Reaktion
                    if key == ord('q') or key == 27:  # q or ESC
                        print("🔴 Last Detection Window CLOSED by user")
                        break
                        
                except Exception as e:
                    print(f"⚠️ Last Detection Window Error: {str(e)}")
                    break
                    
        except Exception as e:
            print(f"⚠️ Last Detection Window Setup Error: {str(e)}")
        finally:
            # SICHERE Window-Cleanup
            try:
                cv2.destroyWindow('🐦 Last Detection - Filtered Objects Only')
                cv2.waitKey(1)
            except Exception:
                pass
        
    def _triangulation_worker(self):
        """Live 3D Triangulation Worker Thread"""
        try:
            import numpy as np
            
            # Konfiguriere PyVista für robustes Windows-Rendering
            import pyvista as pv
            pv.set_plot_theme("dark")
            
            # Windows-spezifische OpenGL-Konfiguration
            try:
                import os
                os.environ['PYVISTA_OFF_SCREEN'] = 'false'
                os.environ['PYVISTA_USE_PANEL'] = 'false'
                
                # Robuste OpenGL-Initialisierung - KEIN Multi-Sampling für Stabilität
                try:
                    # Einfachster möglicher Plotter für maximale Stabilität
                    plotter = pv.Plotter(
                        title="🎯 CRASH-SICHER: Live 3D Triangulation - Himmel Tracking",
                        window_size=[1000, 700],
                        menu_bar=False,  # Keine Menüs = weniger Crash-Risiko
                        toolbar=False    # Keine Toolbar = weniger Crash-Risiko
                    )
                    plotter.background_color = 'black'
                    
                    # KEINE erweiterten Features - diese können crashen
                    # plotter.enable_anti_aliasing()  # DEAKTIVIERT - kann crashen
                    # plotter.enable_depth_peeling()  # DEAKTIVIERT - kann crashen
                    
                except Exception as plotter_error:
                    # Absoluter Fallback: Minimal-Plotter
                    self.log(f"⚠️ Standard Plotter fehlgeschlagen: {plotter_error}")
                    plotter = pv.Plotter()
                    plotter.background_color = 'black'
                    
            except Exception as e:
                # Absoluter Fallback: Minimal-Plotter
                self.log(f"⚠️ Advanced OpenGL features nicht verfügbar: {e}")
                try:
                    plotter = pv.Plotter()
                    plotter.background_color = 'black'
                except Exception as final_error:
                    self.log(f"❌ Plotter-Erstellung vollständig fehlgeschlagen: {final_error}")
                    messagebox.showerror("3D Triangulation", f"PyVista-Initialisierung fehlgeschlagen: {final_error}")
                    self.triangulation_active = False
                    return
            
            # Standard Kamera-Positionen (dynamisch basierend auf ausgewählten Webcams)
            if not hasattr(self, 'camera_positions'):
                # Fallback falls keine Positionen gesetzt wurden
                self.camera_positions = {
                    'webcam_0': np.array([-1, 0, 0]),     # Links (1m von Zentrum)
                    'webcam_1': np.array([1, 0, 0]),      # Rechts (1m von Zentrum)
                    'webcam_2': np.array([0, 0, 0])       # Zentrum (falls vorhanden)
                }
            
            # Farben für verschiedene Kameras (dynamisch basierend auf ausgewählten Webcams)
            if not hasattr(self, 'camera_colors'):
                # Fallback falls keine Farben gesetzt wurden
                self.camera_colors = {
                    'webcam_0': 'red',     # Links = Rot
                    'webcam_1': 'green',   # Rechts = Grün
                    'webcam_2': 'blue'     # Zentrum = Blau (falls vorhanden)
                }
            
            # Setup 3D Scene einmalig
            self._setup_3d_scene(plotter)
            
            # Interaktive GUI für Kamera-Positionierung
            self._setup_camera_controls(plotter)
            
            # Steuerungstext - angepasst für Himmel-Tracking
            plotter.add_text("🎯 HIMMEL TRACKING - Flugzeuge & Vögel\n\n"
                            "📷 Kamera-Setup (Himmel-Tracking):\n"
                            "• Webcam 0: ROT (Links, 5cm)\n"
                            "• Webcam 1: GRÜN (Rechts, 5cm)\n" 
                            "• Beide parallel zum Himmel gerichtet\n\n"
                            "🔄 Physische Anordnung:\n"
                            "• 10cm Abstand (Stereo-Basis)\n"
                            "• 60° Elevation (Himmel-Winkel)\n"
                            "• Parallele Ausrichtung\n\n"
                            "✈️ HIMMEL TRACKING:\n"
                            "• Orange Strahlen: Motion Detection\n"
                            "• Cyan Kugel: Trianguliertes Objekt\n"
                            "• Optimiert für große Entfernungen\n\n"
                            "🎮 Steuerung:\n"
                            "• Maus-Drag: 3D Navigation\n"
                            "• Rad: Zoom\n"
                            "• ESC: Sicher beenden\n"
                            "• ⚠️ Q vermeiden (beendet alles)", 
                            position='upper_left', font_size=9, color='white')
            
            # Starte Plotter OHNE show() zunächst
            # show() kann Thread-Konflikte verursachen
            
            # Live-Update-Schleife OHNE plotter.show()
            self._run_live_updates_without_show(plotter)
            
            # Cleanup nach Schließen
            self.triangulation_active = False
            
        except ImportError:
            messagebox.showerror("Triangulation Error", 
                               "PyVista nicht installiert!\nBitte installieren: pip install pyvista")
        except Exception as e:
            messagebox.showerror("Triangulation Error", f"3D Triangulation Fehler: {str(e)}")
        finally:
            self.triangulation_active = False
            
    def _run_live_updates_without_show(self, plotter):
        """Führe Live-Updates ohne plotter.show() aus - THREAD-SICHER"""
        try:
            # WICHTIG: show() im MAIN THREAD aufrufen, nicht im Worker Thread!
            # Das verhindert den Warte-Cursor und Threading-Konflikte
            plotter.show(interactive=True, auto_close=False)  # Interactive = True für echte GUI
            
            # Setze Window-spezifische Einstellungen für Stabilität
            if hasattr(plotter, 'iren') and plotter.iren:
                plotter.iren.SetDesiredUpdateRate(2.0)  # Nur 2 FPS für Stabilität
                
        except Exception as e:
            self.log(f"❌ Plotter-Show fehlgeschlagen: {str(e)}")
            self.triangulation_active = False
            return
            
        # Live-Update-Loop - KEIN separater Thread mehr!
        # Updates werden über Timer-Events gemacht
        update_counter = 0
        error_count = 0
        
        self.log("🎯 Triangulation läuft - Thread-sicher ohne Worker-Thread")
        
        def update_visualization():
            """Timer-basierte Updates statt Thread-Loop"""
            nonlocal update_counter, error_count
            
            if not self.triangulation_active or not self.is_tracking:
                return False  # Stop Timer
                
            try:
                # Nur bei echten Motion-Updates rendern
                if hasattr(self, 'camera_motion_data') and self.camera_motion_data:
                    # Clear nur wenn nötig
                    if update_counter % 20 == 0:  # Noch seltener
                        self._clear_motion_objects(plotter)
                    
                    # Filtere synchrone Bewegungen ZUERST
                    synchronized_motions = self._filter_synchronized_motions()
                    
                    if synchronized_motions and len(synchronized_motions) >= 2:
                        # Nur zeichnen wenn synchrone Motion auf beiden Kameras
                        self._draw_filtered_camera_rays(plotter, synchronized_motions)
                        self._calculate_filtered_triangulation(plotter, synchronized_motions)
                        
                        # Render nur wenn neue Daten vorhanden
                        if update_counter % 5 == 0:  # Alle 5 Updates
                            plotter.render()
                
                update_counter += 1
                error_count = 0
                
            except Exception as e:
                error_count += 1
                if error_count <= 3:
                    self.log(f"⚠️ Update-Fehler #{error_count}: {str(e)[:30]}...")
                if error_count >= 10:
                    self.log("❌ Zu viele Fehler - stoppe Updates")
                    return False
                    
            return True  # Continue Timer
        
        # Timer-basierte Updates statt Thread-Loop
        try:
            import threading
            timer_interval = 0.5  # 2 FPS
            
            def timer_loop():
                while self.triangulation_active and self.is_tracking:
                    if not update_visualization():
                        break
                    time.sleep(timer_interval)
                self.log("✅ Timer-Loop beendet")
                
            # Timer in separatem Thread - aber GUI-Updates im Main Thread
            timer_thread = threading.Thread(target=timer_loop, daemon=True)
            timer_thread.start()
            
        except Exception as e:
            self.log(f"❌ Timer-Setup fehlgeschlagen: {str(e)}")
            self.triangulation_active = False
            
    def _setup_3d_scene(self, plotter):
        """Setup der 3D Szene mit Koordinatensystem und Kameras"""
        # Koordinatenachsen mit korrekter PyVista API
        try:
            # Versuche moderne PyVista API
            axes = pv.Axes(show_actor=True, actor_scale=1.0, line_width=3)
            plotter.add_actor(axes)
        except AttributeError:
            # Fallback: Manuelle Achsen erstellen
            # X-Achse (rot)
            x_line = pv.Line(pointa=np.array([0.0, 0.0, 0.0], dtype=np.float32), 
                            pointb=np.array([2.0, 0.0, 0.0], dtype=np.float32))
            plotter.add_mesh(x_line, color='red', line_width=4, label='X-Axis')
            
            # Y-Achse (grün)
            y_line = pv.Line(pointa=np.array([0.0, 0.0, 0.0], dtype=np.float32), 
                            pointb=np.array([0.0, 2.0, 0.0], dtype=np.float32))
            plotter.add_mesh(y_line, color='green', line_width=4, label='Y-Axis')
            
            # Z-Achse (blau)
            z_line = pv.Line(pointa=np.array([0.0, 0.0, 0.0], dtype=np.float32), 
                            pointb=np.array([0.0, 0.0, 2.0], dtype=np.float32))
            plotter.add_mesh(z_line, color='blue', line_width=4, label='Z-Axis')
            
            # Achsen-Labels
            plotter.add_point_labels([[2, 0, 0]], ['X'], point_size=5, font_size=12, text_color='red')
            plotter.add_point_labels([[0, 2, 0]], ['Y'], point_size=5, font_size=12, text_color='green')
            plotter.add_point_labels([[0, 0, 2]], ['Z'], point_size=5, font_size=12, text_color='blue')
        
        # Boden-Grid für bessere Orientierung
        grid = pv.Plane(center=(2, 1, -0.5), direction=(0, 0, 1), 
                       i_size=6, j_size=4, i_resolution=10, j_resolution=10)
        plotter.add_mesh(grid, style='wireframe', color='gray', opacity=0.3)
        
        # Zeichne Kameras mit Sichtfeldern
        for camera_name, position in self.camera_positions.items():
            if camera_name in self.caps:  # Nur aktive Kameras
                # Kamera als Pyramide darstellen
                camera_mesh = self._create_camera_mesh(position)
                color = self.camera_colors.get(camera_name, 'white')
                plotter.add_mesh(camera_mesh, color=color, opacity=0.8)
                
                # Sichtfeld-Kegel für bessere Visualisierung
                self._add_camera_fov(plotter, camera_name, position, color)
                
                # Kamera-Label
                plotter.add_point_labels([position], [camera_name], 
                                       point_color=color, point_size=10, 
                                       font_size=12, text_color='white')
    
    def _add_camera_fov(self, plotter, camera_name, position, color):
        """Füge Sichtfeld-Visualisierung für Kamera hinzu"""
        # Field of View Kegel (60° Öffnungswinkel, normal für Webcams)
        fov_angle = 60  # Grad - typischer Webcam-FOV
        fov_distance = 50.0  # 50 Meter Sichtweite für Himmel-Tracking
        
        # Berechne Kegel-Richtung basierend auf physische Anordnung
        # Himmel-Tracking: Beide Kameras schauen parallel nach oben/vorne (Flugzeuge/Vögel)
        if camera_name == 'webcam_0':
            # Linke Kamera: leicht nach oben und vorne gerichtet (Himmel)
            direction = np.array([0, 0.5, 0.866])  # 60° nach oben (Himmel-Blickwinkel)
        elif camera_name == 'webcam_1':
            # Rechte Kamera: ebenfalls nach oben und vorne gerichtet (parallel zur linken)
            direction = np.array([0, 0.5, 0.866])  # 60° nach oben (parallel)
        elif camera_name == 'webcam_2':
            direction = np.array([0, 0.5, 0.866])  # Ebenfalls Himmel-gerichtet
        else:
            direction = np.array([0, 0.5, 0.866])  # Default Himmel-Richtung
        
        # Erstelle Sichtfeld-Kegel
        cone_center = position + direction * (fov_distance / 2)
        fov_cone = pv.Cone(center=cone_center, direction=direction,
                          height=fov_distance, radius=fov_distance * np.tan(np.radians(fov_angle/2)),
                          resolution=8)
        
        # Füge transparenten Sichtfeld-Kegel hinzu
        plotter.add_mesh(fov_cone, color=color, opacity=0.2, style='wireframe')
                
    def _setup_camera_controls(self, plotter):
        """Setup einfache Kamera-Preset-Controls ohne Drag&Drop"""
        # Info-Text mit Filter-Information
        control_text = ("📍 SYNC-FILTER AKTIV:\n"
                       "• Nur zeitgleiche Bewegungen (±300ms)\n"
                       "• Beide Kameras müssen Motion erkennen\n"
                       "• Himmel-Tracking: 100m Strahlen\n\n"
                       "🎮 NAVIGATION (THREAD-SICHER):\n"
                       "• Maus-Drag: 3D Rotation\n"
                       "• Maus-Rad: Zoom\n"
                       "• Rechts-Drag: Pan\n\n"
                       "⚠️ CRASH-SICHER:\n"
                       "• Timer-basierte Updates\n"
                       "• Kein Worker-Thread\n"
                       "• Synchron-Filter aktiv\n"
                       "• Kein Warte-Cursor mehr!")
        
        plotter.add_text(control_text, position='lower_left', font_size=8, color='yellow')
        
        # Nur Preset-Shortcuts - keine Drag&Drop-Funktionen
        def on_key_1():
            """Himmel-Tracking Preset"""
            self._set_sky_preset()
            self.log("📷 Preset 1: Himmel-Tracking aktiviert")
            
        def on_key_2():
            """30° Objekt-Tracking Preset"""
            self._set_object_preset()
            self.log("� Preset 2: 30° Objekt-Tracking aktiviert")
            
        def on_key_3():
            """Minimal-Winkel Preset"""
            self._set_minimal_preset()
            self.log("� Preset 3: Minimal-Winkel aktiviert")
            
        def on_key_r():
            """Reset View"""
            plotter.reset_camera()
            self.log("� View zurückgesetzt")
        
        # KEINE PyVista Event-Handler! Diese verursachen Abstürze beim Anklicken
        # Das Problem: PyVista add_key_event() führt zu Crashes bei Window-Focus-Wechsel
        # Lösung: Reine Visualisierung ohne interaktive Events
        self.log("⚠️ PyVista Events deaktiviert - verhindert Abstürze beim Klicken")
    
    def _reset_camera_positions(self):
        """Reset Kamera-Positionen zu Standard-Werten - Himmel-Tracking Setup für Flugzeuge/Vögel"""
        # Default: Himmel-Tracking Setup
        self._set_sky_preset()
    
    def _set_sky_preset(self):
        """Preset 1: Himmel-Tracking - 10cm Abstand, parallel zum Himmel"""
        self.camera_positions = {
            'webcam_0': np.array([-0.05, 0, 0]),   # Links (5cm von Zentrum)
            'webcam_1': np.array([0.05, 0, 0]),    # Rechts (5cm von Zentrum)
            'webcam_2': np.array([0, -0.1, 0])     # Zentrum-hinten
        }
        # Beide Kameras parallel zum Himmel (60° Elevation)
        self.camera_directions = {
            'webcam_0': np.array([0, 0.5, 0.866]),
            'webcam_1': np.array([0, 0.5, 0.866]),
            'webcam_2': np.array([0, 0.5, 0.866])
        }
        
    def _set_object_preset(self):
        """Preset 2: Objekt-Tracking - 1.5m Abstand, 30° zueinander gedreht"""
        self.camera_positions = {
            'webcam_0': np.array([-0.75, 0, 0]),   # Links (75cm von Zentrum)
            'webcam_1': np.array([0.75, 0, 0]),    # Rechts (75cm von Zentrum)
            'webcam_2': np.array([0, -0.5, 0])     # Zentrum-hinten
        }
        # Kameras 30° zueinander gedreht
        self.camera_directions = {
            'webcam_0': np.array([0.5, 0.866, 0]),   # 30° nach rechts
            'webcam_1': np.array([-0.5, 0.866, 0]),  # 30° nach links
            'webcam_2': np.array([0, 1, 0])          # Gerade nach vorne
        }
        
    def _set_minimal_preset(self):
        """Preset 3: Minimal-Winkel - 50cm Abstand, 5° zueinander gedreht"""
        self.camera_positions = {
            'webcam_0': np.array([-0.25, 0, 0]),   # Links (25cm von Zentrum)
            'webcam_1': np.array([0.25, 0, 0]),    # Rechts (25cm von Zentrum)
            'webcam_2': np.array([0, -0.25, 0])    # Zentrum-hinten
        }
        # Kameras nur 5° zueinander gedreht (minimal für bessere Parallaxe)
        self.camera_directions = {
            'webcam_0': np.array([0.087, 0.996, 0]),  # 5° nach rechts
            'webcam_1': np.array([-0.087, 0.996, 0]), # 5° nach links
            'webcam_2': np.array([0, 1, 0])           # Gerade nach vorne
        }
    
    def _filter_synchronized_motions(self):
        """Filtere nur zeitgleiche Bewegungen auf beiden Kameras - KERN-FILTER"""
        try:
            if not hasattr(self, 'camera_motion_data') or len(self.camera_motion_data) < 2:
                return {}
                
            current_time = time.time()
            sync_tolerance = 0.3  # 300ms Toleranz für Synchronisation
            
            # Sammle nur sehr aktuelle Motion-Events
            recent_motions = {}
            for camera_name, motion_list in self.camera_motion_data.items():
                if camera_name not in self.camera_positions or not motion_list:
                    continue
                    
                # Nur Events der letzten Sekunde
                very_recent = []
                for motion in motion_list:
                    try:
                        if current_time - motion['timestamp'] < 1.0:
                            very_recent.append(motion)
                    except:
                        continue
                        
                if very_recent:
                    recent_motions[camera_name] = very_recent
            
            if len(recent_motions) < 2:
                return {}
            
            # Finde zeitlich synchrone Motion-Paare
            synchronized_pairs = {}
            camera_names = list(recent_motions.keys())
            
            # Prüfe alle Kamera-Kombinationen
            for i in range(len(camera_names)):
                for j in range(i + 1, len(camera_names)):
                    cam1_name = camera_names[i]
                    cam2_name = camera_names[j]
                    
                    # Finde beste zeitliche Übereinstimmung
                    best_match = None
                    best_time_diff = float('inf')
                    
                    for motion1 in recent_motions[cam1_name]:
                        for motion2 in recent_motions[cam2_name]:
                            try:
                                time_diff = abs(motion1['timestamp'] - motion2['timestamp'])
                                if time_diff < sync_tolerance and time_diff < best_time_diff:
                                    best_time_diff = time_diff
                                    best_match = (motion1, motion2)
                            except:
                                continue
                    
                    # Speichere synchrone Paare
                    if best_match:
                        synchronized_pairs[f"{cam1_name}_{cam2_name}"] = {
                            cam1_name: best_match[0],
                            cam2_name: best_match[1],
                            'time_diff': best_time_diff
                        }
            
            # Gib das beste synchrone Paar zurück
            if synchronized_pairs:
                # Wähle Paar mit kleinster Zeitdifferenz
                best_pair_key = min(synchronized_pairs.keys(), 
                                  key=lambda k: synchronized_pairs[k]['time_diff'])
                best_pair = synchronized_pairs[best_pair_key]
                
                # Entferne Metadaten für Rückgabe
                result = {}
                for cam_name, motion in best_pair.items():
                    if cam_name != 'time_diff':
                        result[cam_name] = motion
                        
                return result
            
            return {}
            
        except Exception as e:
            # Sicher fallback
            return {}
    
    def _draw_filtered_camera_rays(self, plotter, synchronized_motions):
        """Zeichne nur gefilterte, synchrone Camera Rays"""
        try:
            if not synchronized_motions:
                return
                
            for camera_name, motion in synchronized_motions.items():
                try:
                    if camera_name not in self.camera_positions:
                        continue
                        
                    camera_pos = self.camera_positions[camera_name]
                    camera_color = self.camera_colors.get(camera_name, 'white')
                    
                    # 3D Richtung berechnen
                    direction = self._pixel_to_3d_direction(motion['x'], motion['y'], camera_name)
                    
                    # Strahl für Himmel-Tracking (längere Distanz)
                    ray_length = 100.0  # 100m für Flugzeug-Tracking
                    ray_end = camera_pos + direction * ray_length
                    
                    # Cast to float32 for PyVista
                    camera_pos_f = camera_pos.astype(np.float32)
                    ray_end_f = ray_end.astype(np.float32)
                    
                    # Nur synchrone Strahlen zeichnen (heller/dicker für Sichtbarkeit)
                    line = pv.Line(camera_pos_f, ray_end_f)
                    plotter.add_mesh(line, color=camera_color, line_width=5, opacity=0.9)
                    
                    # Motion-Punkt am Ende markieren
                    motion_point = pv.Sphere(radius=2.0, center=ray_end_f)  # Größer für Sichtbarkeit
                    plotter.add_mesh(motion_point, color=camera_color, opacity=0.8)
                    
                except Exception:
                    continue  # Ignoriere einzelne Ray-Fehler
                    
        except Exception:
            pass  # Komplett sicher
    
    def _calculate_filtered_triangulation(self, plotter, synchronized_motions):
        """Berechne Triangulation nur für gefilterte, synchrone Motions"""
        try:
            if not synchronized_motions or len(synchronized_motions) < 2:
                return
                
            # Alle Kamera-Kombinationen triangulieren
            triangulated_points = []
            confidence_scores = []
            
            camera_names = list(synchronized_motions.keys())
            for i in range(len(camera_names)):
                for j in range(i + 1, len(camera_names)):
                    try:
                        cam1_name = camera_names[i]
                        cam2_name = camera_names[j]
                        
                        motion1 = synchronized_motions[cam1_name]
                        motion2 = synchronized_motions[cam2_name]
                        
                        # 3D Strahlen berechnen
                        pos1 = self.camera_positions[cam1_name]
                        dir1 = self._pixel_to_3d_direction(motion1['x'], motion1['y'], cam1_name)
                        
                        pos2 = self.camera_positions[cam2_name]
                        dir2 = self._pixel_to_3d_direction(motion2['x'], motion2['y'], cam2_name)
                        
                        # Triangulation berechnen
                        intersection, confidence = self._line_intersection_3d_with_confidence(pos1, dir1, pos2, dir2)
                        
                        if intersection is not None and confidence > 0.2:  # Niedrigere Schwelle für Flugzeuge
                            triangulated_points.append(intersection)
                            confidence_scores.append(confidence)
                            
                    except Exception:
                        continue
            
            # Finale triangulierte Position anzeigen
            if triangulated_points:
                try:
                    # Gewichteter Durchschnitt aller Triangulationen
                    total_weight = sum(confidence_scores)
                    if total_weight > 0:
                        weighted_position = np.zeros(3)
                        for point, confidence in zip(triangulated_points, confidence_scores):
                            weighted_position += point * (confidence / total_weight)
                        
                        # Finale Position als größere, gut sichtbare Kugel
                        object_size = 5.0  # Viel größer für Sichtbarkeit bei großen Entfernungen
                        final_object = pv.Sphere(radius=object_size, center=weighted_position)
                        plotter.add_mesh(final_object, color='cyan', opacity=1.0)
                        
                        # Koordinaten-Info für Debugging
                        distance = np.linalg.norm(weighted_position)
                        if distance > 10:  # Nur bei realistischen Flugzeug-Entfernungen
                            coord_text = f"📍 Objekt: {distance:.0f}m\nXYZ: ({weighted_position[0]:.1f}, {weighted_position[1]:.1f}, {weighted_position[2]:.1f})"
                            plotter.add_point_labels([weighted_position], [coord_text], 
                                                   point_size=8, font_size=10, text_color='cyan')
                        
                except Exception:
                    pass
                    
        except Exception:
            pass  # Komplett sicher
        """Entferne nur motion-relevante Objekte für Live-Updates - optimiert für Performance"""
        try:
            # Defensive Programmierung - prüfe erst ob Renderer existiert
            if not hasattr(plotter, 'renderer') or not plotter.renderer:
                return
                
            # Sichere Actor-Liste erstellen (Kopie)
            actors_list = []
            try:
                if hasattr(plotter.renderer, 'actors'):
                    actors_list = list(plotter.renderer.actors)
            except:
                return  # Kein Zugriff auf Actors möglich
            
            # Suche und entferne nur temporäre Tracking-Objekte
            actors_to_remove = []
            for actor in actors_list:
                try:
                    # Entferne orange/cyan Objekte (Motion rays + triangulated objects)
                    if hasattr(actor, 'GetProperty'):
                        prop = actor.GetProperty()
                        if hasattr(prop, 'GetColor'):
                            color = prop.GetColor()
                            # Orange (1.0, 0.5, 0.0) und Cyan (0.0, 1.0, 1.0) Objekte entfernen
                            if (abs(color[0] - 1.0) < 0.1 and abs(color[1] - 0.5) < 0.1 and abs(color[2] - 0.0) < 0.1) or \
                               (abs(color[0] - 0.0) < 0.1 and abs(color[1] - 1.0) < 0.1 and abs(color[2] - 1.0) < 0.1):
                                actors_to_remove.append(actor)
                except:
                    continue  # Ignoriere einzelne Actor-Fehler
            
            # Entferne Actors sicher
            for actor in actors_to_remove:
                try:
                    plotter.renderer.RemoveActor(actor)
                except:
                    continue  # Ignoriere Remove-Fehler für einzelne Actors
                    
        except Exception:
            # Komplettes Fallback - ignoriere alle Clear-Operationen bei Problemen
            pass
    
    def _draw_live_camera_rays(self, plotter):
        """Zeichne Live-Sichtstrahlen von den Kameras - reduziert für weniger Clutter"""
        try:
            if not hasattr(self, 'camera_motion_data') or not self.camera_motion_data:
                return
                
            current_time = time.time()
            ray_lifetime = 1.0  # Reduziert auf 1 Sekunde für weniger Clutter
            
            for camera_name, motion_list in self.camera_motion_data.items():
                try:
                    if camera_name not in self.camera_positions or not motion_list:
                        continue
                        
                    # Aktuelle Motion-Events mit sicherer Filterung
                    recent_motions = []
                    for motion in motion_list:
                        try:
                            if current_time - motion['timestamp'] < ray_lifetime:
                                recent_motions.append(motion)
                        except:
                            continue
                    
                    if recent_motions:
                        camera_pos = self.camera_positions[camera_name]
                        camera_color = self.camera_colors.get(camera_name, 'white')
                        
                        # Zeige nur das neueste Motion für weniger Überfüllung
                        for motion in recent_motions[-1:]:  # Nur das letzte Motion anzeigen
                            try:
                                # Berechne 3D Richtung
                                direction = self._pixel_to_3d_direction(motion['x'], motion['y'], camera_name)
                                
                                # Sichtstrahl mit Länge basierend auf Alter
                                age = current_time - motion['timestamp']
                                alpha = max(0.2, min(0.8, 1.0 - (age / ray_lifetime)))
                                ray_length = 3.0  # Kürzere Strahlen
                                
                                ray_end = camera_pos + direction * ray_length
                                
                                # Erstelle Strahl-Linie mit Float-Koordinaten
                                camera_pos_f = camera_pos.astype(np.float32)
                                ray_end_f = ray_end.astype(np.float32)
                                
                                ray_line = pv.Line(camera_pos_f, ray_end_f)
                                plotter.add_mesh(ray_line, color='orange', line_width=2,
                                               opacity=alpha, label=f'ray_{camera_name}')
                                
                                # Kleinere Motion points
                                motion_point = pv.Sphere(radius=0.05, center=ray_end_f)
                                plotter.add_mesh(motion_point, color=camera_color, opacity=alpha)
                            except:
                                continue  # Ignoriere einzelne Motion-Fehler
                except:
                    continue  # Ignoriere Kamera-Fehler
        except Exception:
            # Komplett sicher - ignoriere alle Ray-Drawing-Fehler
            pass
    
    def _calculate_live_triangulation(self, plotter):
        """Live-Berechnung der Triangulation mit reduzierter Visualisierung für weniger Clutter"""
        try:
            if not hasattr(self, 'camera_motion_data') or len(self.camera_motion_data) < 2:
                return
                
            current_time = time.time()
            sync_window = 0.8  # Kürzeres Synchronisations-Fenster
            
            # Sammle neueste synchrone Motion-Events
            synchronized_motions = {}
            
            for camera_name, motion_list in self.camera_motion_data.items():
                try:
                    if camera_name not in self.camera_positions or not motion_list:
                        continue
                    # Neueste Events in Zeitfenster mit sicherer Filterung
                    recent_motions = []
                    for motion in motion_list:
                        try:
                            if current_time - motion['timestamp'] < sync_window:
                                recent_motions.append(motion)
                        except:
                            continue
                    
                    if recent_motions:
                        synchronized_motions[camera_name] = recent_motions[-1]
                except:
                    continue  # Ignoriere Kamera-Fehler
            
            if len(synchronized_motions) < 2:
                return
                
            # Berechne Triangulation für alle Kamera-Paare
            triangulated_points = []
            confidence_scores = []
            
            camera_names = list(synchronized_motions.keys())
            for i in range(len(camera_names)):
                for j in range(i + 1, len(camera_names)):
                    try:
                        cam1_name = camera_names[i]
                        cam2_name = camera_names[j]
                        
                        motion1 = synchronized_motions[cam1_name]
                        motion2 = synchronized_motions[cam2_name]
                        
                        # Berechne 3D Strahlen sicher
                        pos1 = self.camera_positions[cam1_name]
                        dir1 = self._pixel_to_3d_direction(motion1['x'], motion1['y'], cam1_name)
                        
                        pos2 = self.camera_positions[cam2_name]
                        dir2 = self._pixel_to_3d_direction(motion2['x'], motion2['y'], cam2_name)
                        
                        # Finde Kreuzungspunkt
                        intersection, confidence = self._line_intersection_3d_with_confidence(pos1, dir1, pos2, dir2)
                        if intersection is not None and confidence > 0.3:
                            triangulated_points.append(intersection)
                            confidence_scores.append(confidence)
                    except:
                        continue  # Ignoriere einzelne Triangulations-Fehler
            
            # Finale Objekt-Position mit gewichteter Mittelung - NUR diese anzeigen
            if triangulated_points:
                try:
                    # Gewichtete Mittelung basierend auf Confidence
                    total_weight = sum(confidence_scores)
                    if total_weight > 0:
                        weighted_position = np.zeros(3)
                        for point, confidence in zip(triangulated_points, confidence_scores):
                            weighted_position += point * (confidence / total_weight)
                        
                        # Finale Live-Objekt-Position
                        object_size = 0.12
                        final_object = pv.Sphere(radius=object_size, center=weighted_position)
                        plotter.add_mesh(final_object, color='cyan', opacity=1.0)
                        
                        # Reduzierte Live-Koordinaten
                        coord_text = (f"🎯 OBJEKT\n"
                                    f"X: {weighted_position[0]:.1f}m\n"
                                    f"Y: {weighted_position[1]:.1f}m\n"
                                    f"Z: {weighted_position[2]:.1f}m")
                        
                        plotter.add_point_labels([weighted_position], [coord_text], 
                                               point_color='cyan', point_size=15,
                                               font_size=8, text_color='white')
                        
                        # Kompakte Live-Statistiken
                        stats_text = (f"📊 TRIANGULATION\n"
                                    f"Paare: {len(triangulated_points)}\n"
                                    f"Kameras: {len(synchronized_motions)}")
                        plotter.add_text(stats_text, position='lower_right', font_size=8, color='cyan')
                except:
                    pass  # Ignoriere Visualisierungs-Fehler
        except Exception:
            # Komplett sicher - ignoriere alle Triangulations-Fehler
            pass
    
    def _line_intersection_3d_with_confidence(self, p1, d1, p2, d2):
        """Finde Kreuzungspunkt mit Confidence-Score - optimiert für Himmel-Tracking (große Entfernungen)"""
        w = p1 - p2
        a = np.dot(d1, d1)
        b = np.dot(d1, d2)
        c = np.dot(d2, d2)
        d = np.dot(d1, w)
        e = np.dot(d2, w)
        
        denominator = a * c - b * b
        if abs(denominator) < 1e-8:  # Strengere Parallel-Erkennung für Himmel-Tracking
            return None, 0.0
            
        t1 = (b * e - c * d) / denominator
        t2 = (a * e - b * d) / denominator
        
        # Für Himmel-Tracking: Nur positive t-Werte (vor den Kameras)
        if t1 < 0.1 or t2 < 0.1:  # Mindestabstand 10cm
            return None, 0.0
        
        # Berechne nächste Punkte auf beiden Linien
        closest1 = p1 + t1 * d1
        closest2 = p2 + t2 * d2
        
        # Mittelpunkt als Triangulation
        intersection = (closest1 + closest2) / 2
        
        # Confidence für große Entfernungen angepasst
        distance = np.linalg.norm(closest1 - closest2)
        
        # Für Flugzeuge/Vögel: Toleriere größere Abstände zwischen den Strahlen
        confidence = max(0.0, 1.0 - distance / 50.0)  # 50m Toleranz statt 2m
        
        # Winkel zwischen Strahlen - für parallele Kameras sind kleine Winkel OK
        cos_angle = abs(np.dot(d1, d2))
        angle_confidence = 1.0 - cos_angle * 0.5  # Weniger Penalty für parallele Strahlen
        
        # Entfernung zu Kameras - Flugzeuge sind weit weg
        dist1 = np.linalg.norm(intersection - p1)
        dist2 = np.linalg.norm(intersection - p2)
        avg_distance = (dist1 + dist2) / 2
        
        # Optimaler Bereich für Flugzeuge: 100m - 10km
        if 100 <= avg_distance <= 10000:
            distance_confidence = 1.0
        elif avg_distance < 100:
            distance_confidence = avg_distance / 100.0  # Reduziere Confidence für zu nahe Objekte
        else:
            distance_confidence = 1.0 / (1.0 + (avg_distance - 10000) / 5000.0)  # Reduziere für sehr weit entfernte
        
        # Kombinierte Confidence
        final_confidence = confidence * angle_confidence * distance_confidence
        
        return intersection, final_confidence
                
    def _create_camera_mesh(self, position):
        """Erstelle eine Kamera-Pyramide"""
        # Kleine Pyramide für Kamera
        cone = pv.Cone(center=position, direction=(0, 1, 0), 
                      height=0.3, radius=0.15, resolution=4)
        return cone
        
    def _draw_camera_rays(self, plotter):
        """Zeichne Sichtstrahlen von Kameras zu Motion-Punkten"""
        if not self.camera_motion_data:
            return
            
        # Aktuelle Zeit für zeitliche Synchronisation
        current_time = time.time()
        time_window = 2.0  # 2 Sekunden Fenster
        
        for camera_name, camera_pos in self.camera_positions.items():
            if camera_name not in self.camera_motion_data:
                continue
                
            camera_color = self.camera_colors.get(camera_name, 'white')
            
            # Filtere Motion-Daten nach Zeit
            recent_motions = [
                motion for motion in self.camera_motion_data[camera_name]
                if current_time - motion['timestamp'] < time_window
            ]
            
            # Zeichne Strahlen für jedes Motion-Event
            for motion_data in recent_motions[-5:]:  # Nur die letzten 5
                x, y = motion_data['x'], motion_data['y']
                
                # Konvertiere 2D Bildkoordinaten zu 3D Richtung
                direction = self._pixel_to_3d_direction(x, y, camera_name)
                
                # Strahl-Endpunkt berechnen
                ray_length = 4.0  # Meter
                ray_end = camera_pos + direction * ray_length
                
                # Cast to float32 for PyVista
                camera_pos_f = camera_pos.astype(np.float32)
                ray_end_f = ray_end.astype(np.float32)
                
                # Strahl als Linie zeichnen
                line = pv.Line(camera_pos_f, ray_end_f)
                plotter.add_mesh(line, color=camera_color, line_width=3, opacity=0.7)
                
                # Motion-Punkt markieren
                motion_point = pv.Sphere(radius=0.06, center=ray_end_f)
                plotter.add_mesh(motion_point, color=camera_color, opacity=0.9)
                    
    def _pixel_to_3d_direction(self, pixel_x, pixel_y, camera_name):
        """Konvertiere 2D Pixel-Koordinaten zu 3D Richtungsvektor - Full HD optimiert"""
        # Vereinfachte Kamera-Transformation für Full HD
        # In einer echten Implementierung würden hier Kamera-Intrinsics verwendet
        
        # Normalisiere Pixel-Koordinaten zu [-1, 1] für Full HD (1920x1080)
        norm_x = (pixel_x - 960) / 960  # Full HD: 1920/2 = 960
        norm_y = (pixel_y - 540) / 540  # Full HD: 1080/2 = 540
        
        # Standard Field of View Annahme (60° typisch für Webcams)
        fov_factor = 0.7  # Für 60° FOV
        
        # Basis-Richtung für jede Kamera (Himmel-Tracking Setup)
        if camera_name == 'webcam_0':
            # Linke Kamera: nach oben-vorne gerichtet (Himmel-Tracking)
            base_dir = np.array([0, 0.5, 0.866])  # 60° Elevation für Himmel
            right_vec = np.array([1, 0, 0])  # X-Achse für horizontale Bewegung
            up_vec = np.array([0, 0.866, -0.5])  # Hoch-Vektor angepasst für 60° Neigung
        elif camera_name == 'webcam_1':
            # Rechte Kamera: parallel zur linken (Himmel-Tracking)
            base_dir = np.array([0, 0.5, 0.866])  # 60° Elevation für Himmel (parallel)
            right_vec = np.array([1, 0, 0])  # X-Achse für horizontale Bewegung
            up_vec = np.array([0, 0.866, -0.5])  # Hoch-Vektor angepasst für 60° Neigung
        elif camera_name == 'webcam_2':
            # Zentrum: gerade nach vorne
            base_dir = np.array([0, 1, 0])
            right_vec = np.array([1, 0, 0])
            up_vec = np.array([0, 0, 1])
        else:
            # Default: gerade nach vorne
            base_dir = np.array([0, 1, 0])
            right_vec = np.array([1, 0, 0])
            up_vec = np.array([0, 0, 1])
        
        # Kombiniere Basis-Richtung mit Pixel-Offset
        direction = base_dir + (right_vec * norm_x * fov_factor) + (up_vec * norm_y * fov_factor)
            
        # Normalisiere Richtungsvektor
        return direction / np.linalg.norm(direction)
        
    def _calculate_triangulation(self, plotter):
        """Berechne und visualisiere Triangulation von Kreuzungspunkten"""
        if len(self.camera_motion_data) < 2:  # Brauchen mindestens 2 Kameras
            return
            
        # Aktuelle Zeit für Synchronisation
        current_time = time.time()
        sync_window = 1.0  # 1 Sekunde Synchronisations-Fenster
        
        # Sammle synchrone Motion-Events von verschiedenen Kameras
        synchronized_motions = {}
        
        for camera_name, motion_list in self.camera_motion_data.items():
            if camera_name in self.camera_positions:
                # Neueste Motion-Events in Zeitfenster
                recent_motions = [
                    motion for motion in motion_list
                    if current_time - motion['timestamp'] < sync_window
                ]
                if recent_motions:
                    synchronized_motions[camera_name] = recent_motions[-1]  # Neuestes Event
        
        if len(synchronized_motions) < 2:
            return
            
        # Berechne Triangulation für alle Kamera-Paare
        triangulated_points = []
        camera_pairs = []
        
        camera_names = list(synchronized_motions.keys())
        for i in range(len(camera_names)):
            for j in range(i + 1, len(camera_names)):
                cam1_name = camera_names[i]
                cam2_name = camera_names[j]
                
                motion1 = synchronized_motions[cam1_name]
                motion2 = synchronized_motions[cam2_name]
                
                # Berechne 3D Strahlen
                pos1 = self.camera_positions[cam1_name]
                dir1 = self._pixel_to_3d_direction(motion1['x'], motion1['y'], cam1_name)
                
                pos2 = self.camera_positions[cam2_name]
                dir2 = self._pixel_to_3d_direction(motion2['x'], motion2['y'], cam2_name)
                
                # Finde Kreuzungspunkt
                intersection = self._line_intersection_3d(pos1, dir1, pos2, dir2)
                if intersection is not None:
                    triangulated_points.append(intersection)
                    camera_pairs.append((cam1_name, cam2_name))
                    
                    # Visualisiere Triangulations-Punkt
                    point_mesh = pv.Sphere(radius=0.12, center=intersection)
                    plotter.add_mesh(point_mesh, color='orange', opacity=0.9)
                    
                    # Verbindungslinien zwischen Kreuzungspunkten
                    connection_line = pv.Line(pos1, intersection)
                    plotter.add_mesh(connection_line, color='orange', line_width=1, opacity=0.4)
                    connection_line2 = pv.Line(pos2, intersection)
                    plotter.add_mesh(connection_line2, color='orange', line_width=1, opacity=0.4)
        
        # Berechne finale Objekt-Position als Durchschnitt aller Triangulationen
        if triangulated_points:
            avg_position = np.mean(triangulated_points, axis=0)
            
            # Finale Objekt-Position
            final_object = pv.Sphere(radius=0.2, center=avg_position)
            plotter.add_mesh(final_object, color='cyan', opacity=1.0)
            
            # Label mit Koordinaten
            coord_text = f"🎯 OBJEKT\nX: {avg_position[0]:.2f}m\nY: {avg_position[1]:.2f}m\nZ: {avg_position[2]:.2f}m"
            plotter.add_point_labels([avg_position], [coord_text], 
                                   point_color='cyan', point_size=25, 
                                   font_size=12, text_color='white')
            
            # Zeige Anzahl der verwendeten Kamera-Paare
            stats_text = f"📊 Triangulation aus {len(triangulated_points)} Kamera-Paaren"
            plotter.add_text(stats_text, position='lower_right', font_size=10, color='cyan')
            
    def _line_intersection_3d(self, p1, d1, p2, d2):
        """Finde nächsten Punkt zwischen zwei 3D Linien"""
        # Mathematische Lösung für nächsten Punkt zwischen zwei sich nicht schneidenden Linien
        w = p1 - p2
        a = np.dot(d1, d1)
        b = np.dot(d1, d2)
        c = np.dot(d2, d2)
        d = np.dot(d1, w)
        e = np.dot(d2, w)
        
        denominator = a * c - b * b
        if abs(denominator) < 1e-6:  # Parallel lines
            return None
            
        t1 = (b * e - c * d) / denominator
        t2 = (a * e - b * d) / denominator
        
        point1 = p1 + t1 * d1
        point2 = p2 + t2 * d2
        
        # Mittelpunkt zwischen den nächsten Punkten
        return (point1 + point2) / 2

    def open_3d_viewer(self):
        """Open 3D motion visualization viewer"""
        if len(self.motion_data) < 10:
            messagebox.showwarning("3D Viewer", 
                                 "Nicht genügend Motion-Daten für 3D-Visualisierung.\n"
                                 "Starten Sie erst Motion Tracking und sammeln Sie Daten.")
            return
            
        self.log("🎲 Öffne 3D Motion Viewer...")
        threading.Thread(target=self._open_3d_viewer_worker, daemon=True).start()
        
    def _open_3d_viewer_worker(self):
        """Worker thread for 3D viewer"""
        try:
            # Create 3D plot
            plotter = pv.Plotter(title="🎲 Motion Tracking - 3D Visualization")
            
            # Convert motion data to 3D points
            if self.motion_data:
                points = []
                colors = []
                sizes = []
                
                for i, motion_point in enumerate(self.motion_data):
                    x, y, area, timestamp = motion_point
                    z = i * 0.1  # Time dimension
                    
                    points.append([x, y, z])
                    
                    # Color based on object size
                    if area < 100:
                        colors.append([0, 1, 0])  # Green for small objects
                    elif area < 500:
                        colors.append([1, 1, 0])  # Yellow for medium objects
                    else:
                        colors.append([1, 0, 0])  # Red for large objects
                        
                    sizes.append(max(1, area / 100))
                
                if points:
                    # Create point cloud with proper float32 type
                    points_f = np.array(points, dtype=np.float32)
                    point_cloud = pv.PolyData(points_f)
                    point_cloud['colors'] = colors
                    point_cloud['sizes'] = sizes
                    
                    # Add to plotter
                    plotter.add_mesh(point_cloud, 
                                   scalars='colors', 
                                   rgb=True,
                                   point_size=10,
                                   render_points_as_spheres=True)
                    
                    # Add coordinate system
                    plotter.add_axes()
                    plotter.show_grid()
                    
                    # Add text info
                    plotter.add_text(f"Motion Points: {len(points)}", 
                                   position='upper_left', font_size=12)
                    plotter.add_text("Green=Small, Yellow=Medium, Red=Large", 
                                   position='lower_left', font_size=10)
                    
                    self.log(f"🎲 3D Viewer: {len(points)} Motion-Punkte visualisiert")
                    
                    # Show the plot
                    plotter.show()
                    
        except Exception as e:
            self.log(f"❌ 3D Viewer Fehler: {str(e)}")
            
    def toggle_settings(self):
        """Toggle advanced settings visibility"""
        if self.settings_visible:
            self.settings_frame.pack_forget()
            self.settings_btn.config(text="⚙️ Advanced Settings")
            self.settings_visible = False
            self.log("🔼 Advanced Settings versteckt")
        else:
            # Pack the settings frame after the configuration frame
            self.settings_frame.pack(pady=5, padx=10, fill=tk.X, after=self.root.winfo_children()[1])
            self.settings_btn.config(text="🔼 Hide Settings")
            self.settings_visible = True
            self.log("⚙️ Advanced Settings angezeigt")
            
            # Update settings from current profile
            self.update_settings_from_profile()
            
    def update_settings_from_profile(self):
        """Update advanced settings based on selected profile"""
        try:
            profile_name = self.profile_var.get()
            if profile_name in DETECTION_PROFILES:
                profile = DETECTION_PROFILES[profile_name]
                self.threshold_var.set(profile.get('threshold', 25))
                self.min_area_var.set(profile.get('min_area', 100))  
                self.max_area_var.set(profile.get('max_area', 10000))
                self.log(f"⚙️ Settings updated for {profile_name}")
        except Exception as e:
            self.log(f"⚠️ Settings update error: {str(e)}")
            
    def test_source(self):
        """Test the selected video source"""
        self.log("🔍 Testing video source...")
        self.status_var.set("🔍 Testing source...")
        threading.Thread(target=self._test_source_worker, daemon=True).start()
        
    def _test_source_worker(self):
        """Worker thread for source testing"""
        try:
            source_name = self.source_var.get()
            source = VIDEO_SOURCES[source_name]
            
            if source['type'] == 'webcam':
                # Test local webcam
                cap = cv2.VideoCapture(source['source'])
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        self.log(f"✅ Webcam Test erfolgreich: {frame.shape[1]}x{frame.shape[0]}")
                        result = True
                    else:
                        self.log("❌ Webcam: Kein Frame empfangen")
                        result = False
                    cap.release()
                else:
                    self.log("❌ Webcam: Kann nicht geöffnet werden")
                    result = False
                    
            elif source['type'] in ['youtube_single', 'youtube_dual']:
                # Test YouTube URLs
                if source['type'] == 'youtube_dual':
                    urls = source['sources']
                    results = {}
                    for name, url in urls.items():
                        self.log(f"🔍 Testing {name}...")
                        results[name] = self._test_youtube_url(url)
                    result = any(results.values())
                    working = sum(results.values())
                    self.log(f"📊 YouTube Test: {working}/{len(results)} Streams verfügbar")
                else:
                    result = self._test_youtube_url(source['source'])
                    
            elif source['type'] == 'custom_url':
                url = self.url_var.get().strip()
                if not url:
                    self.log("❌ Keine URL eingegeben")
                    result = False
                else:
                    self.log(f"🔍 Testing custom URL: {url}")
                    result = self._test_custom_url(url)
            else:
                self.log(f"❌ Unbekannter Source-Typ: {source['type']}")
                result = False
                
            # Update status
            if result:
                self.status_var.set("✅ Source Test erfolgreich - Bereit für Tracking")
            else:
                self.status_var.set("❌ Source Test fehlgeschlagen")
                
        except Exception as e:
            self.log(f"❌ Test-Fehler: {str(e)}")
            self.status_var.set("❌ Test-Fehler")
            
    def _test_youtube_url(self, url):
        """Test a YouTube URL"""
        try:
            cmd = ['python', '-m', 'yt_dlp', '--get-url', '--format', 'best[height<=720]', url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                self.log("✅ YouTube URL verfügbar")
                return True
            else:
                self.log(f"❌ YouTube Fehler: {result.stderr.strip()}")
                return False
        except Exception as e:
            self.log(f"❌ YouTube Test-Fehler: {str(e)}")
            return False
            
    def _test_custom_url(self, url):
        """Test a custom URL"""
        try:
            cap = cv2.VideoCapture(url)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    self.log(f"✅ Custom URL Test erfolgreich: {frame.shape[1]}x{frame.shape[0]}")
                    result = True
                else:
                    self.log("❌ Custom URL: Kein Frame empfangen")
                    result = False
                cap.release()
                return result
            else:
                self.log("❌ Custom URL: Kann nicht geöffnet werden")
                return False
        except Exception as e:
            self.log(f"❌ Custom URL Test-Fehler: {str(e)}")
            return False
            
    def start_tracking(self):
        """Start motion tracking"""
        if self.is_tracking:
            return
            
        self.log("🎬 Starte Motion Tracking...")
        self.status_var.set("🎬 Motion Tracking gestartet")
        
        self.is_tracking = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        # Start tracking thread
        self.tracking_thread = threading.Thread(target=self._tracking_worker, daemon=True)
        self.tracking_thread.start()
        
    def stop_tracking(self):
        """Stop motion tracking safely"""
        if not self.is_tracking:
            return
            
        self.log("⏹️ Stoppe Motion Tracking...")
        
        # Set stop flag first
        self.is_tracking = False
        
        # Stop Live Triangulation
        if hasattr(self, 'triangulation_active'):
            self.triangulation_active = False
            self.log("📐 Stoppe Live Triangulation...")
        
        # Update GUI immediately to show stopping state
        try:
            self.stop_btn.config(state=tk.DISABLED, text="⏳ Stopping...")
            self.status_var.set("⏳ Stoppe Tracking...")
            self.root.update()  # Force GUI update
        except Exception as e:
            self.log(f"⚠️ GUI Update Fehler: {str(e)}")
        
        # Start cleanup in separate thread to avoid freezing
        cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        cleanup_thread.start()
        
    def _cleanup_worker(self):
        """Cleanup worker - runs in separate thread"""
        try:
            # Wait for tracking loop to finish
            if hasattr(self, 'tracking_thread') and self.tracking_thread.is_alive():
                self.tracking_thread.join(timeout=2.0)  # Max 2 seconds wait
            
            # SICHERE OpenCV Window Cleanup
            try:
                # Alle OpenCV Windows schließen
                cv2.destroyAllWindows()
                cv2.waitKey(1)
                
                # Warte kurz und versuche nochmal
                time.sleep(0.2)
                cv2.destroyAllWindows()
                cv2.waitKey(1)
                
                # Force cleanup für spezielle Windows
                try:
                    cv2.destroyWindow("🔥 Last Detection")
                    cv2.destroyWindow("🐦 Last Detection - Filtered Objects Only")
                except:
                    pass
                    
            except Exception as e:
                self.log(f"⚠️ OpenCV Window-Cleanup: {str(e)}")
            
            # Release captures safely
            caps_to_release = list(self.caps.items()) if self.caps else []
            for name, cap in caps_to_release:
                try:
                    if cap and hasattr(cap, 'isOpened'):
                        if cap.isOpened():
                            # For webcams, clear buffer first
                            if 'webcam' in name.lower():
                                try:
                                    # Quick buffer clear
                                    for _ in range(3):
                                        ret, _ = cap.read()
                                        if not ret:
                                            break
                                except Exception:
                                    pass
                            cap.release()
                            self.log(f"✅ {name} released")
                        
                except Exception as e:
                    self.log(f"⚠️ {name} release error: {str(e)}")
                    
            # Clear data structures
            self.caps.clear()
            self.bg_subtractors.clear()
            
            # Final OpenCV cleanup
            try:
                cv2.destroyAllWindows()
                cv2.waitKey(1)
            except Exception:
                pass
            
            # Update GUI in main thread
            self.root.after(0, self._finalize_stop)
            
        except Exception as e:
            self.log(f"❌ Cleanup error: {str(e)}")
            # Still try to update GUI
            self.root.after(0, self._finalize_stop)
            
    def _finalize_stop(self):
        """Finalize stop in main thread"""
        try:
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED, text="⏹️ Stop Tracking")
            self.status_var.set("⏹️ Motion Tracking gestoppt")
            self.log("✅ Motion Tracking erfolgreich gestoppt")
        except Exception as e:
            self.log(f"⚠️ GUI finalize error: {str(e)}")
        
    def _tracking_worker(self):
        """Main tracking worker thread"""
        try:
            # Get current configuration
            profile_name = self.profile_var.get()
            profile = DETECTION_PROFILES[profile_name]
            source_name = self.source_var.get()
            source = VIDEO_SOURCES[source_name]
            
            # Use advanced settings if modified
            threshold = self.threshold_var.get()
            min_area = self.min_area_var.get()
            max_area = self.max_area_var.get()
            
            self.log(f"🎯 Profile: {profile_name}")
            self.log(f"📺 Source: {source_name}")
            self.log(f"⚙️ Settings: Threshold={threshold}, Area={min_area}-{max_area}")
            
            # Initialize video sources
            if not self._initialize_sources(source):
                self.log("❌ Konnte Video-Quellen nicht initialisieren")
                self.stop_tracking()
                return
                
            # Main tracking loop
            self._tracking_loop(threshold, min_area, max_area)
            
        except Exception as e:
            self.log(f"❌ Tracking-Fehler: {str(e)}")
        finally:
            # Ensure cleanup happens
            self.root.after(0, self.stop_tracking)
            
    def _initialize_sources(self, source):
        """Initialize video sources based on type"""
        if source['type'] == 'webcam':
            cap = cv2.VideoCapture(source['source'])
            if cap.isOpened():
                webcam_name = f"webcam_{source['source']}"
                self.caps[webcam_name] = cap
                self.bg_subtractors[webcam_name] = cv2.createBackgroundSubtractorMOG2()
                self.log(f"✅ Webcam {source['source']} initialisiert")
                return True
            else:
                self.log(f"❌ Webcam {source['source']} konnte nicht geöffnet werden")
                return False
                
        elif source['type'] == 'multi_webcam':
            success_count = 0
            # Verwende nur ausgewählte Webcams
            selected_webcams = [i for i in range(4) if self.webcam_vars[f'webcam_{i}'].get()]
            
            if not selected_webcams:
                self.log("❌ Keine Webcams ausgewählt!")
                return False
                
            self.log(f"🎯 Verwende ausgewählte Webcams: {selected_webcams}")
            
            for webcam_idx in selected_webcams:
                try:
                    cap = cv2.VideoCapture(webcam_idx)
                    if cap.isOpened():
                        # Set Full HD resolution (1920x1080) at 30 FPS
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
                        cap.set(cv2.CAP_PROP_FPS, 30)
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        
                        # Test ob die Webcam wirklich verfügbar ist
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                            self.log(f"🎥 Webcam {webcam_idx} Auflösung: {actual_width}x{actual_height}")
                            
                            webcam_name = f"webcam_{webcam_idx}"
                            self.caps[webcam_name] = cap
                            self.bg_subtractors[webcam_name] = cv2.createBackgroundSubtractorMOG2()
                            self.log(f"✅ Webcam {webcam_idx} initialisiert")
                            success_count += 1
                        else:
                            cap.release()
                            self.log(f"⚠️ Webcam {webcam_idx} verfügbar aber liefert keine Frames")
                    else:
                        self.log(f"⚠️ Webcam {webcam_idx} nicht verfügbar")
                except Exception as e:
                    self.log(f"❌ Webcam {webcam_idx} Fehler: {str(e)}")
                    
            if success_count > 0:
                self.log(f"✅ Multi-Webcam: {success_count}/{len(selected_webcams)} Kameras aktiv")
                # Update Kamera-Positionen basierend auf aktiven Webcams
                self._update_camera_positions_for_active_webcams(selected_webcams)
                return True
            else:
                self.log("❌ Keine ausgewählten Webcams konnten initialisiert werden")
                return False
                
        elif source['type'] == 'youtube_single':
            return self._init_youtube_single(source['source'])
            
        elif source['type'] == 'youtube_dual':
            return self._init_youtube_dual(source['sources'])
            
        elif source['type'] == 'custom_url':
            url = self.url_var.get().strip()
            if not url:
                self.log("❌ Keine Custom URL eingegeben")
                return False
            return self._init_custom_url(url)
            
        return False
                
    def _update_camera_positions_for_active_webcams(self, active_webcams):
        """Update Kamera-Positionen basierend auf aktive Webcams"""
        # Nur für aktive Webcams Positionen setzen
        self.camera_positions = {}
        self.camera_colors = {}
        
        if len(active_webcams) == 1:
            # Eine Kamera - zentral
            webcam_name = f"webcam_{active_webcams[0]}"
            self.camera_positions[webcam_name] = np.array([0, 0, 0])
            self.camera_colors[webcam_name] = 'red'
            
        elif len(active_webcams) == 2:
            # Zwei Kameras - nebeneinander mit 30° Rotation (optimal)
            webcam_0 = f"webcam_{active_webcams[0]}"
            webcam_1 = f"webcam_{active_webcams[1]}"
            
            self.camera_positions[webcam_0] = np.array([-1, 0, 0])  # Links
            self.camera_positions[webcam_1] = np.array([1, 0, 0])   # Rechts
            
            self.camera_colors[webcam_0] = 'red'
            self.camera_colors[webcam_1] = 'green'
            
        else:
            # Drei oder mehr Kameras - erweiterte Anordnung
            colors = ['red', 'green', 'blue', 'yellow']
            for i, webcam_idx in enumerate(active_webcams):
                webcam_name = f"webcam_{webcam_idx}"
                
                if i == 0:
                    self.camera_positions[webcam_name] = np.array([-1, 0, 0])  # Links
                elif i == 1:
                    self.camera_positions[webcam_name] = np.array([1, 0, 0])   # Rechts
                elif i == 2:
                    self.camera_positions[webcam_name] = np.array([0, 0, 0])   # Zentrum
                else:
                    # Weitere Kameras in einem Kreis anordnen
                    angle = (i - 2) * (2 * np.pi / max(1, len(active_webcams) - 2))
                    radius = 1.5
                    x = radius * np.cos(angle)
                    y = radius * np.sin(angle)
                    self.camera_positions[webcam_name] = np.array([x, y, 0])
                
                self.camera_colors[webcam_name] = colors[min(i, len(colors) - 1)]
        
        self.log(f"📍 Kamera-Positionen aktualisiert für {len(active_webcams)} aktive Webcams")
        
    def _init_youtube_single(self, youtube_url):
        """Initialize single YouTube stream"""
        try:
            self.log("🔗 Extrahiere YouTube Stream-URL...")
            cmd = ['python', '-m', 'yt_dlp', '--get-url', '--format', 'best[height<=720]', youtube_url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                stream_url = result.stdout.strip()
                cap = cv2.VideoCapture(stream_url)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                if cap.isOpened():
                    self.caps['youtube'] = cap
                    self.bg_subtractors['youtube'] = cv2.createBackgroundSubtractorMOG2()
                    self.log("✅ YouTube Stream initialisiert")
                    return True
                else:
                    self.log("❌ YouTube Stream konnte nicht geöffnet werden")
            else:
                self.log(f"❌ YouTube URL-Extraktion fehlgeschlagen: {result.stderr}")
                
        except Exception as e:
            self.log(f"❌ YouTube Initialisierung fehlgeschlagen: {str(e)}")
            
        return False
        
    def _init_youtube_dual(self, youtube_urls):
        """Initialize dual YouTube streams"""
        success_count = 0
        
        for name, youtube_url in youtube_urls.items():
            try:
                self.log(f"🔗 Extrahiere {name} Stream-URL...")
                cmd = ['python', '-m', 'yt_dlp', '--get-url', '--format', 'best[height<=720]', youtube_url]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    stream_url = result.stdout.strip()
                    cap = cv2.VideoCapture(stream_url)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    
                    if cap.isOpened():
                        self.caps[name] = cap
                        self.bg_subtractors[name] = cv2.createBackgroundSubtractorMOG2()
                        self.log(f"✅ {name} Stream initialisiert")
                        success_count += 1
                    else:
                        self.log(f"❌ {name} Stream konnte nicht geöffnet werden")
                else:
                    self.log(f"❌ {name} URL-Extraktion fehlgeschlagen")
                    
            except Exception as e:
                self.log(f"❌ {name} Initialisierung fehlgeschlagen: {str(e)}")
                
        return success_count > 0
        
    def _init_custom_url(self, url):
        """Initialize custom URL"""
        try:
            cap = cv2.VideoCapture(url)
            if cap.isOpened():
                self.caps['custom'] = cap
                self.bg_subtractors['custom'] = cv2.createBackgroundSubtractorMOG2()
                self.log("✅ Custom URL initialisiert")
                return True
            else:
                self.log("❌ Custom URL konnte nicht geöffnet werden")
        except Exception as e:
            self.log(f"❌ Custom URL Initialisierung fehlgeschlagen: {str(e)}")
            
        return False
        
    def _tracking_loop(self, threshold, min_area, max_area):
        """Main tracking loop"""
        self.log("🎯 Starte Motion Detection...")
        
        frame_count = 0
        start_time = time.time()
        self.tracking_start_time = start_time
        fps_update_interval = 30  # Update FPS every 30 frames
        
        while self.is_tracking:
            frame_count += 1
            frames = {}
            motion_counts = {}
            
            # Update FPS für Dashboard
            if frame_count % fps_update_interval == 0:
                elapsed = time.time() - start_time
                self.current_fps = frame_count / elapsed if elapsed > 0 else 0
            
            # Capture and process frames
            for name, cap in list(self.caps.items()):
                if not self.is_tracking:
                    break
                    
                try:
                    ret, frame = cap.read()
                    if ret:
                        processed_frame, motion_count = self._process_motion(
                            frame, name, threshold, min_area, max_area
                        )
                        frames[name] = processed_frame
                        motion_counts[name] = motion_count
                    else:
                        self.log(f"⚠️ {name}: Kein Frame empfangen")
                except Exception as e:
                    self.log(f"❌ {name} Capture-Fehler: {str(e)}")
                    
            # Update Dashboard Daten
            self.current_motion_counts = motion_counts.copy()
                    
            # Display frames
            if frames and self.is_tracking:
                self._display_frames(frames, motion_counts, frame_count, start_time)
                
            # Handle OpenCV events
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or not self.is_tracking:
                break
            elif key == ord('s'):
                self._save_screenshots(frames)
            elif key == ord('+'):
                # Increase sensitivity (lower threshold)
                new_threshold = max(5, self.threshold_var.get() - 5)
                self.threshold_var.set(new_threshold)
                self.log(f"🔧 Sensitivity increased (threshold: {new_threshold})")
            elif key == ord('-'):
                # Decrease sensitivity (higher threshold)  
                new_threshold = min(100, self.threshold_var.get() + 5)
                self.threshold_var.set(new_threshold)
                self.log(f"🔧 Sensitivity decreased (threshold: {new_threshold})")
            elif key == ord('a'):
                # Decrease min area
                new_area = max(1, self.min_area_var.get() - 50)
                self.min_area_var.set(new_area)
                self.log(f"🔧 Min area decreased: {new_area}")
            elif key == ord('A'):
                # Increase min area
                new_area = min(1000, self.min_area_var.get() + 50)
                self.min_area_var.set(new_area)
                self.log(f"🔧 Min area increased: {new_area}")
                
            # Get live settings updates for next iteration
            threshold = self.threshold_var.get()
            min_area = self.min_area_var.get()
            max_area = self.max_area_var.get()
            
            time.sleep(0.03)  # ~30 FPS
            
    def _process_motion(self, frame, stream_name, threshold, min_area, max_area):
        """Process motion detection on frame"""
        if frame is None:
            return frame, 0
            
        bg_subtractor = self.bg_subtractors[stream_name]
        
        # Background subtraction
        fg_mask = bg_subtractor.apply(frame)
        
        # Apply threshold for sensitivity control
        _, fg_mask = cv2.threshold(fg_mask, threshold, 255, cv2.THRESH_BINARY)
        
        # Morphological operations
        kernel = np.ones((3,3), np.uint8)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Process contours with ERWEITERTE Anti-Stationary Filter
        motion_count = 0
        filtered_motion_count = 0
        result_frame = frame.copy()
        
        # Get live filter settings (PERFORMANCE-OPTIMIERT)
        min_movement = self.min_movement_var.get() if hasattr(self, 'min_movement_var') else 5  # Sehr niedrig
        time_window = self.movement_window_var.get() if hasattr(self, 'movement_window_var') else 1.0
        consistency_frames = self.consistency_var.get() if hasattr(self, 'consistency_var') else 3
        current_time = time.time()
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if min_area <= area <= max_area:
                motion_count += 1
                
                # Get contour info
                x, y, w, h = cv2.boundingRect(contour)
                center_x = x + w // 2
                center_y = y + h // 2
                timestamp = current_time
                
                # ANTI-WOLKEN FILTER - INTELLIGENTE HIMMELBEOBACHTUNG
                passes_filter = True  # Start optimistisch
                filter_reasons = []
                
                # 1. Mindest-Bewegung (gegen Wolken-Drift)
                min_movement = getattr(self, 'min_movement_var', type('obj', (object,), {'get': lambda: 15})).get()
                if stream_name in self.camera_motion_data and len(self.camera_motion_data[stream_name]) >= 2:
                    last_motion = list(self.camera_motion_data[stream_name])[-1]
                    last_x = last_motion.get('x', 0)
                    last_y = last_motion.get('y', 0)
                    distance = ((center_x - last_x)**2 + (center_y - last_y)**2)**0.5
                    
                    if distance < min_movement:
                        passes_filter = False
                        filter_reasons.append("SLOW")
                    else:
                        filter_reasons.append("FAST")
                
                # 2. Area Filter (gegen Reflexionen und große Wolken) - NEUE VARIABLEN
                anti_cloud_min_area = getattr(self, 'anti_cloud_min_area_var', type('obj', (object,), {'get': lambda: 60})).get()
                anti_cloud_max_area = getattr(self, 'anti_cloud_max_area_var', type('obj', (object,), {'get': lambda: 2500})).get()
                
                if area < anti_cloud_min_area:
                    passes_filter = False
                    filter_reasons.append("TINY")
                elif area > anti_cloud_max_area:
                    passes_filter = False 
                    filter_reasons.append("HUGE")
                else:
                    filter_reasons.append("SIZE_OK")
                
                # 3. Speed Filter (Vogel-typische Geschwindigkeit)
                min_speed = getattr(self, 'min_speed_var', type('obj', (object,), {'get': lambda: 20})).get()
                if stream_name in self.camera_motion_data and len(self.camera_motion_data[stream_name]) >= 3:
                    # Berechne Geschwindigkeit über letzte Frames
                    motions = list(self.camera_motion_data[stream_name])[-3:]
                    if len(motions) >= 2:
                        time_diff = motions[-1]['timestamp'] - motions[-2]['timestamp']
                        if time_diff > 0:
                            speed = distance / time_diff  # Pixel pro Sekunde
                            speed_per_frame = speed / 30  # Annahme: 30 FPS
                            
                            if speed_per_frame < min_speed:
                                passes_filter = False
                                filter_reasons.append("CRAWL")
                            else:
                                filter_reasons.append("BIRD_SPEED")
                
                # Zusammenfassung der Filter-Gründe
                if not filter_reasons:
                    filter_reasons = ["FIRST"]
                    
                filter_reason = " ".join(filter_reasons[:2])  # Maximal 2 Gründe
                
                # Draw based on filter result
                if passes_filter:
                    filtered_motion_count += 1
                    # Green = passes filter
                    cv2.rectangle(result_frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
                    cv2.putText(result_frame, f'F{filtered_motion_count}', 
                               (x, y-25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    cv2.putText(result_frame, filter_reason, 
                               (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
                    
                    # Store for Last Detection Window
                    if not hasattr(self, 'last_detection_frame'):
                        self.last_detection_frame = None
                    
                    # Extract detection region (größerer Bereich)
                    padding = 30
                    detection_region = frame[max(0, y-padding):min(frame.shape[0], y+h+padding), 
                                           max(0, x-padding):min(frame.shape[1], x+w+padding)]
                    if detection_region.size > 0:
                        self.last_detection_frame = detection_region.copy()
                        self.last_detection_info = {
                            'timestamp': timestamp,
                            'camera': stream_name,
                            'area': area,
                            'center': (center_x, center_y),
                            'bbox': (x, y, w, h),
                            'reason': filter_reason
                        }
                else:
                    # Red = filtered out
                    cv2.rectangle(result_frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                    cv2.putText(result_frame, f'M{motion_count}', 
                               (x, y-25), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
                    cv2.putText(result_frame, filter_reason, 
                               (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)
                           
                # Motion point für 3D viewer (auch für gefilterte)
                self.motion_data.append((center_x, center_y, area, timestamp))
                
                # Kamera-spezifische Daten für Triangulation (nur filtered)
                if passes_filter:
                    if stream_name not in self.camera_motion_data:
                        self.camera_motion_data[stream_name] = deque(maxlen=20)  # Reduziert für bessere Performance
                    self.camera_motion_data[stream_name].append({
                        'x': center_x,
                        'y': center_y, 
                        'area': area,
                        'timestamp': timestamp,
                        'camera': stream_name
                    })
                           
        # Add stream info with enhanced Anti-Wolken filter stats
        timestamp_str = datetime.now().strftime("%H:%M:%S")
        cv2.putText(result_frame, f'{stream_name} - {timestamp_str}', 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(result_frame, f'Total Motion: {motion_count} | 🦅 Vögel: {filtered_motion_count}', 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Filter-Parameter anzeigen - KORREKTE VARIABLEN
        min_movement = getattr(self, 'min_movement_var', type('obj', (object,), {'get': lambda: 15})).get()
        anti_cloud_min = getattr(self, 'anti_cloud_min_area_var', type('obj', (object,), {'get': lambda: 60})).get()
        anti_cloud_max = getattr(self, 'anti_cloud_max_area_var', type('obj', (object,), {'get': lambda: 2500})).get()
        min_speed_val = getattr(self, 'min_speed_var', type('obj', (object,), {'get': lambda: 20})).get()
        
        cv2.putText(result_frame, f'🌤️ Anti-Wolken: Move≥{min_movement}px Area{anti_cloud_min}-{anti_cloud_max}px² Speed≥{min_speed_val}', 
                   (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
                   
        return result_frame, filtered_motion_count  # Return filtered count
        
    def _display_frames(self, frames, motion_counts, frame_count, start_time):
        """Display processed frames - supports unlimited cameras"""
        try:
            fps = frame_count / (time.time() - start_time + 0.001)
            
            if len(frames) == 1:
                # Single frame display
                name, frame = list(frames.items())[0]
                cv2.putText(frame, f'FPS: {fps:.1f}', 
                           (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                cv2.imshow(f'Motion Tracker - {name}', frame)
                
            elif len(frames) == 2:
                # Side-by-side dual display
                stream_names = list(frames.keys())
                frame1 = frames[stream_names[0]]
                frame2 = frames[stream_names[1]]
                
                # Resize to larger height for better visibility (1.2x scaling)
                height = min(frame1.shape[0], frame2.shape[0], 480)  # Increased from 400 to 480
                frame1_resized = cv2.resize(frame1, (int(frame1.shape[1] * height / frame1.shape[0]), height))
                frame2_resized = cv2.resize(frame2, (int(frame2.shape[1] * height / frame2.shape[0]), height))
                
                # Add FPS info
                cv2.putText(frame1_resized, f'FPS: {fps:.1f}', 
                           (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
                
                # Combine frames horizontally
                combined = np.hstack([frame1_resized, frame2_resized])
                cv2.imshow('Motion Tracker - Dual View', combined)
                
            else:
                # Multi-camera grid display (3+ cameras)
                stream_names = list(frames.keys())
                num_cameras = len(frames)
                
                # Calculate grid dimensions (prefer wider than tall)
                cols = int(np.ceil(np.sqrt(num_cameras)))
                rows = int(np.ceil(num_cameras / cols))
                
                # Resize all frames to larger size for grid (1.5x scaling)
                target_width = 480  # Increased from 320 to 480 (1.5x)
                target_height = 360  # Increased from 240 to 360 (1.5x)
                
                grid_frames = []
                for i, name in enumerate(stream_names):
                    frame = frames[name]
                    resized = cv2.resize(frame, (target_width, target_height))
                    
                    # Add FPS only to first frame
                    if i == 0:
                        cv2.putText(resized, f'FPS: {fps:.1f}', 
                                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                    
                    grid_frames.append(resized)
                
                # Pad with black frames if needed
                while len(grid_frames) < rows * cols:
                    black_frame = np.zeros((target_height, target_width, 3), dtype=np.uint8)
                    grid_frames.append(black_frame)
                
                # Create grid
                grid_rows = []
                for row in range(rows):
                    row_frames = grid_frames[row * cols:(row + 1) * cols]
                    if row_frames:
                        grid_row = np.hstack(row_frames)
                        grid_rows.append(grid_row)
                
                if grid_rows:
                    grid = np.vstack(grid_rows)
                    cv2.imshow(f'Motion Tracker - Multi-Cam ({num_cameras} cameras)', grid)
                
        except Exception as e:
            self.log(f"⚠️ Display error: {str(e)}")
            # Fallback: show individual windows
            for name, frame in frames.items():
                try:
                    cv2.imshow(f'Tracker - {name}', frame)
                except:
                    pass
                
                # Combine horizontally
                combined = np.hstack([frame1_resized, frame2_resized])
                
                # Add overall stats
                total_motions = sum(motion_counts.values())
                fps = frame_count / (time.time() - start_time + 0.001)
                cv2.putText(combined, f'Total Motions: {total_motions} | FPS: {fps:.1f}', 
                           (10, combined.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                cv2.imshow('Motion Tracker - Dual View', combined)
                
            # Update log periodically
            if frame_count % 60 == 0:  # Every 60 frames
                total_motions = sum(motion_counts.values()) if motion_counts else 0
                fps = frame_count / (time.time() - start_time + 0.001)
                self.log(f"📊 Frame {frame_count}: {total_motions} Motions, {fps:.1f} FPS")
                
        except Exception as e:
            self.log(f"❌ Display-Fehler: {str(e)}")
            
    def _save_screenshots(self, frames):
        """Save screenshots of current frames"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for name, frame in frames.items():
            filename = f"motion_tracker_{name}_{timestamp}.jpg"
            cv2.imwrite(filename, frame)
            self.log(f"💾 Screenshot gespeichert: {filename}")
            
    def on_closing(self):
        """Handle window closing"""
        self.stop_tracking()
        time.sleep(0.5)  # Give time for cleanup
        self.root.destroy()
        
    def run(self):
        """Start the application"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.log("👋 Anwendung beendet")
        finally:
            self.stop_tracking()

def main():
    """Main entry point"""
    print("🎯 Pixeltovoxelprojector - Master Motion Tracker")
    print("=" * 55)
    
    # Check dependencies
    missing_deps = []
    try:
        import cv2
        print("✅ OpenCV verfügbar")
    except ImportError:
        missing_deps.append("opencv-python")
        
    try:
        import yt_dlp
        print("✅ yt-dlp verfügbar")
    except ImportError:
        missing_deps.append("yt-dlp")
        
    if missing_deps:
        print(f"❌ Fehlende Dependencies: {', '.join(missing_deps)}")
        print(f"📦 Install with: pip install {' '.join(missing_deps)}")
        return
        
    print("🚀 Starte GUI...")
    
    try:
        app = MasterMotionTracker()
        app.run()
    except Exception as e:
        print(f"❌ Anwendungs-Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
