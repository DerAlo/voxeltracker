#!/usr/bin/env python3
"""
BIRD & MOSQUITO TRACKER - Optimiert und Vereinfacht
===================================================

Spezialisiert für:
- Vogel-Tracking (lokale Webcams)
- Muecken-Tracking (lokale Webcams)
- 3D-Triangulation mit matplotlib
- Maximale Aufloesung und Performance

Alle unnoetige Features entfernt, Code aufgeraeumt!
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import cv2
import numpy as np
import threading
import time
from datetime import datetime
from collections import deque
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

print("🎯 Bird & Mosquito Tracker - Optimiert und Vereinfacht")
print("✅ OpenCV verfügbar")
print("✅ matplotlib verfügbar - stabile 3D-Triangulation")


class Stable3DTriangulation:
    """Crash-sichere 3D Triangulation mit matplotlib"""
    
    def __init__(self, tracker):
        self.tracker = tracker
        self.is_active = False
        self.fig = None
        self.ax = None
        
        # Kamera-Setup
        self.camera_positions = {
            'webcam_0': np.array([-0.05, 0, 0]),   # Links (5cm)
            'webcam_1': np.array([0.05, 0, 0]),    # Rechts (5cm)
        }
        
        self.camera_colors = {
            'webcam_0': 'red',     # Links = Rot
            'webcam_1': 'green',   # Rechts = Gruen  
        }
        
    def start_triangulation(self):
        """Starte stabile 3D-Triangulation"""
        if self.is_active:
            print("⚠️ Triangulation läuft bereits!")
            return
            
        print("🚀 Starte STABILE 3D-Triangulation...")
        self.is_active = True
        
        # Erstelle matplotlib 3D-Plot
        plt.style.use('dark_background')
        self.fig = plt.figure(figsize=(14, 10))  # Groesser fuer bessere Sicht
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        # Setup 3D-Szene
        self._setup_3d_scene()
        
        # Timer fuer Live-Updates  
        self.timer = self.fig.canvas.new_timer(interval=400)  # 2.5 FPS
        self.timer.add_callback(self._update_visualization)
        self.timer.start()
        
        # Window-Event fuer sauberes Schliessen
        self.fig.canvas.mpl_connect('close_event', self._on_close)
        
        plt.show()
        
    def _setup_3d_scene(self):
        """Setup 3D-Szene mit Kameras und Koordinatensystem"""
        self.ax.clear()
        self.ax.set_facecolor('black')
        
        # Titel
        self.ax.set_title('🎯 STABILE TRIANGULATION - Vogel/Muecken Tracking\n'
                         '✅ Crash-sicher | 🔄 Sync-Filter aktiv', 
                         color='cyan', fontsize=14, pad=20)
        
        # Achsen-Setup
        self.ax.set_xlabel('X (m)', color='red', fontsize=12)
        self.ax.set_ylabel('Y (m)', color='green', fontsize=12)  
        self.ax.set_zlabel('Z (m)', color='blue', fontsize=12)
        
        # Achsen-Limits fuer Tracking
        self.ax.set_xlim([-3, 3])
        self.ax.set_ylim([-2, 8])
        self.ax.set_zlim([-2, 8])
        
        # Koordinatenachsen zeichnen
        # X-Achse (rot)
        self.ax.plot([0, 3], [0, 0], [0, 0], 'r-', linewidth=4, alpha=0.8)
        self.ax.text(3.2, 0, 0, 'X', color='red', fontsize=12, weight='bold')
        
        # Y-Achse (gruen)
        self.ax.plot([0, 0], [0, 3], [0, 0], 'g-', linewidth=4, alpha=0.8)
        self.ax.text(0, 3.2, 0, 'Y', color='green', fontsize=12, weight='bold')
        
        # Z-Achse (blau)
        self.ax.plot([0, 0], [0, 0], [0, 3], 'b-', linewidth=4, alpha=0.8)
        self.ax.text(0, 0, 3.2, 'Z', color='blue', fontsize=12, weight='bold')
        
        # Boden-Grid
        xx, yy = np.meshgrid(np.linspace(-3, 3, 7), np.linspace(-2, 8, 11))
        zz = np.zeros_like(xx) - 0.5
        self.ax.plot_wireframe(xx, yy, zz, alpha=0.2, color='gray')
        
        # Zeichne Kameras
        for camera_name, position in self.camera_positions.items():
            if hasattr(self.tracker, 'caps') and camera_name in self.tracker.caps:
                color = self.camera_colors.get(camera_name, 'white')
                
                # Kamera als groesseren Punkt
                self.ax.scatter(*position, color=color, s=150, alpha=1.0, 
                              marker='s', edgecolors='white', linewidth=2)
                
                # Kamera-Label
                self.ax.text(position[0], position[1], position[2] + 0.15, 
                           camera_name.replace('webcam_', 'CAM '), 
                           color='white', fontsize=11, weight='bold',
                           bbox=dict(boxstyle="round,pad=0.3", facecolor=color, alpha=0.8))
                
                # Sichtfeld-Kegel
                self._draw_camera_fov(position, color)
        
        # Info-Text
        info_text = ("📍 SYNC-FILTER AKTIV:\n"
                    "• Nur zeitgleiche Bewegungen (±200ms)\n" 
                    "• Beide Kameras muessen Motion erkennen\n"
                    "• Optimiert fuer Voegel und Muecken\n\n"
                    "⚠️ STABIL-MODUS:\n"
                    "• matplotlib statt PyVista\n"
                    "• Maximale Aufloesung\n"
                    "• Crash-sicher!")
                    
        self.ax.text2D(0.02, 0.98, info_text, transform=self.ax.transAxes,
                      fontsize=9, color='yellow', verticalalignment='top',
                      bbox=dict(boxstyle="round,pad=0.4", facecolor='black', alpha=0.8))
        
    def _draw_camera_fov(self, position, color):
        """Zeichne Sichtfeld-Kegel fuer Kamera"""
        # Tracking-Richtung
        direction = np.array([0, 0.7, 0.7])  # 45° nach oben
        fov_distance = 4.0
        
        # Kegel-Endpunkt
        end_point = position + direction * fov_distance
        
        # Sichtstrahl
        self.ax.plot([position[0], end_point[0]],
                    [position[1], end_point[1]], 
                    [position[2], end_point[2]], 
                    color=color, alpha=0.4, linewidth=3)
        
    def _update_visualization(self):
        """Live-Update der Visualization - THREAD-SICHER"""
        try:
            if not self.is_active:
                return
                
            # Pruefe ob Motion-Daten vorhanden
            if not hasattr(self.tracker, 'camera_motion_data'):
                return
                
            # Synchrone Motion-Filter anwenden
            synchronized_motions = self._filter_synchronized_motions()
            
            if synchronized_motions and len(synchronized_motions) >= 2:
                # Loesche alte Motion-Objekte
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
        """Filtere nur zeitgleiche Bewegungen"""
        try:
            if not hasattr(self.tracker, 'camera_motion_data') or \
               len(self.tracker.camera_motion_data) < 2:
                return {}
                
            current_time = time.time()
            sync_tolerance = 0.2  # 200ms Toleranz - schneller
            
            # Sammle aktuelle Motion-Events
            recent_motions = {}
            for camera_name, motion_list in self.tracker.camera_motion_data.items():
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
            
            # Finde beste zeitliche Uebereinstimmung
            camera_names = list(recent_motions.keys())
            best_match = None
            best_time_diff = float('inf')
            
            for i in range(len(camera_names)):
                for j in range(i + 1, len(camera_names)):
                    cam1_name = camera_names[i]
                    cam2_name = camera_names[j]
                    
                    for motion1 in recent_motions[cam1_name]:
                        for motion2 in recent_motions[cam2_name]:
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
                
                # Strahl fuer Tracking
                ray_length = 5.0
                ray_end = camera_pos + direction * ray_length
                
                # Strahl zeichnen
                self.ax.plot([camera_pos[0], ray_end[0]],
                           [camera_pos[1], ray_end[1]], 
                           [camera_pos[2], ray_end[2]], 
                           color=camera_color, linewidth=4, alpha=0.9)
                
                # Motion-Punkt markieren
                self.ax.scatter(*ray_end, color=camera_color, s=100, alpha=1.0)
                
        except Exception:
            pass
    
    def _calculate_and_draw_triangulation(self, synchronized_motions):
        """Berechne und zeichne Triangulation"""
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
                        
                        if intersection is not None and confidence > 0.3:
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
                    
                    # Finale Position als grosse Kugel
                    self.ax.scatter(*weighted_position, color='cyan', s=250, alpha=1.0, 
                                  marker='o', edgecolors='white', linewidth=3)
                    
                    # Koordinaten-Info
                    distance = np.linalg.norm(weighted_position)
                    if distance > 0.5:  # Nur bei realistischen Entfernungen
                        coord_text = f"📍 {distance:.1f}m\n({weighted_position[0]:.1f}, {weighted_position[1]:.1f}, {weighted_position[2]:.1f})"
                        self.ax.text(weighted_position[0], weighted_position[1], weighted_position[2] + 0.3,
                                   coord_text, color='cyan', fontsize=10, ha='center', weight='bold')
                    
        except Exception:
            pass
    
    def _pixel_to_3d_direction(self, pixel_x, pixel_y, camera_name):
        """Konvertiere 2D Pixel zu 3D Richtung"""
        # Normalisiere Pixel-Koordinaten (angepasst fuer hohe Aufloesung)
        norm_x = (pixel_x - 960) / 960  # Annahme: 1920x1080
        norm_y = (pixel_y - 540) / 540
        
        # FOV-Faktor
        fov_factor = 0.8  # 70° FOV
        
        # Tracking: Beide Kameras parallel nach oben/vorne
        base_dir = np.array([0, 0.7, 0.7])  # 45° nach oben
        right_vec = np.array([1, 0, 0])
        up_vec = np.array([0, 0.7, -0.7])
        
        # Richtung berechnen
        direction = base_dir + (right_vec * norm_x * fov_factor) + (up_vec * norm_y * fov_factor)
        
        return direction / np.linalg.norm(direction)
    
    def _line_intersection_3d_with_confidence(self, p1, d1, p2, d2):
        """3D Linien-Intersection mit Confidence"""
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
        
        # Naechste Punkte auf beiden Linien
        closest1 = p1 + t1 * d1
        closest2 = p2 + t2 * d2
        
        # Mittelpunkt als Triangulation
        intersection = (closest1 + closest2) / 2
        
        # Confidence fuer Entfernungen
        distance = np.linalg.norm(closest1 - closest2)
        confidence = max(0.0, 1.0 - distance / 8.0)  # 8m Toleranz
        
        return intersection, confidence
    
    def _on_close(self, event):
        """Sauberes Schliessen"""
        print("✅ Stabile Triangulation beendet")
        self.is_active = False
        if hasattr(self, 'timer'):
            self.timer.stop()


class BirdMosquitoTracker:
    """Spezialisierter Tracker fuer Voegel und Muecken"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎯 Bird & Mosquito Tracker - Optimiert")
        self.root.geometry("1000x700")  # Groesseres Fenster
        
        # Tracking state
        self.is_tracking = False
        self.caps = {}
        self.bg_subtractors = {}
        self.camera_motion_data = {}
        self.motion_data = []
        self.last_detection_frame = None
        self.last_detection_info = None
        
        # Performance optimiert
        self.frame_skip = 1  # Verarbeite jeden Frame
        self.current_frame_count = 0
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup der Benutzeroberflaeche"""
        
        # Header
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        title_label = ttk.Label(header_frame, 
                               text="🎯 Bird & Mosquito Tracker - Optimiert und Vereinfacht",
                               font=('Arial', 16, 'bold'))
        title_label.pack()
        
        subtitle_label = ttk.Label(header_frame, 
                                  text="Spezialisiert für Voegel und Muecken | Maximale Aufloesung | Performance-optimiert",
                                  font=('Arial', 10))
        subtitle_label.pack()
        
        # Hauptbereich
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Control Panel
        control_frame = ttk.LabelFrame(main_frame, text="🎮 Steuerung")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Tracking Mode
        mode_frame = ttk.Frame(control_frame)
        mode_frame.pack(pady=10)
        
        ttk.Label(mode_frame, text="Tracking-Modus:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.mode_var = tk.StringVar(value="Voegel")
        mode_combo = ttk.Combobox(mode_frame, textvariable=self.mode_var, 
                                 values=["Voegel", "Muecken"], state="readonly", width=15)
        mode_combo.pack(side=tk.LEFT, padx=(0, 20))
        mode_combo.bind('<<ComboboxSelected>>', self._on_mode_change)
        
        # Buttons
        button_frame = ttk.Frame(mode_frame)
        button_frame.pack(side=tk.LEFT)
        
        self.start_button = ttk.Button(button_frame, text="🚀 Start Tracking", 
                                      command=self._toggle_tracking)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(button_frame, text="📊 3D Triangulation", 
                  command=self._open_triangulation).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(button_frame, text="📷 Last Detection", 
                  command=self._show_last_detection).pack(side=tk.LEFT)
        
        # Settings in zwei Spalten
        settings_frame = ttk.LabelFrame(main_frame, text="🔧 Einstellungen")
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        # Linke Spalte - Basis-Detection
        left_frame = ttk.Frame(settings_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 5), pady=10)
        
        ttk.Label(left_frame, text="📹 Basis Motion Detection", 
                 font=('Arial', 10, 'bold')).pack()
        
        # Threshold - OPTIMIERT fuer hohe Aufloesung
        self._create_slider(left_frame, "🎯 Empfindlichkeit:", 
                           "threshold_var", 12, 5, 80, 
                           "Niedriger = empfindlicher")
        
        # Min area - OPTIMIERT fuer hohe Aufloesung
        self._create_slider(left_frame, "📏 Min Objektgroesse (px²):", 
                           "min_area_var", 20, 10, 300, 
                           "Filtert zu kleine Objekte")
        
        # Max area - OPTIMIERT fuer hohe Aufloesung
        self._create_slider(left_frame, "📐 Max Objektgroesse (px²):", 
                           "max_area_var", 5000, 1000, 15000, 
                           "Filtert zu grosse Objekte")
        
        # Rechte Spalte - Anti-Wolken Filter
        right_frame = ttk.Frame(settings_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 10), pady=10)
        
        ttk.Label(right_frame, text="🌤️ Anti-Wolken Filter", 
                 font=('Arial', 10, 'bold')).pack()
        
        # Movement filter
        self._create_slider(right_frame, "🎯 Min Bewegung (px):", 
                           "min_movement_var", 12, 5, 50, 
                           "Filtert langsame Bewegungen")
        
        # Anti cloud min area
        self._create_slider(right_frame, "📏 Anti-Wolken Min Area:", 
                           "anti_cloud_min_area_var", 40, 20, 200, 
                           "Gegen kleine Reflexionen")
        
        # Anti cloud max area
        self._create_slider(right_frame, "☁️ Anti-Wolken Max Area:", 
                           "anti_cloud_max_area_var", 3000, 1500, 8000, 
                           "Gegen grosse Wolken")
        
        # Speed filter
        self._create_slider(right_frame, "🦅 Min Geschwindigkeit:", 
                           "min_speed_var", 15, 8, 80, 
                           "Vogel-typische Geschwindigkeit")
        
        # Status
        status_frame = ttk.LabelFrame(main_frame, text="📊 Status")
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_var = tk.StringVar(value="💤 Bereit - Modus waehlen und 'Start Tracking' klicken")
        ttk.Label(status_frame, textvariable=self.status_var).pack(pady=5)
        
        # Log
        log_frame = ttk.LabelFrame(main_frame, text="📝 Log")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Initial mode setup
        self._on_mode_change()
        
    def _create_slider(self, parent, label, var_name, default_val, min_val, max_val, help_text):
        """Erstelle einen Parameter-Slider"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(frame, text=label).pack(anchor=tk.W)
        
        # Variable erstellen
        var = tk.IntVar(value=default_val)
        setattr(self, var_name, var)
        
        slider_frame = ttk.Frame(frame)
        slider_frame.pack(fill=tk.X)
        
        scale = ttk.Scale(slider_frame, from_=min_val, to=max_val, 
                         variable=var, orient=tk.HORIZONTAL)
        scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        value_label = ttk.Label(slider_frame, textvariable=var, width=4)
        value_label.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Help text
        help_label = ttk.Label(frame, text=help_text, font=('Arial', 8), foreground='gray')
        help_label.pack(anchor=tk.W)
        
    def _on_mode_change(self, event=None):
        """Handle mode change"""
        mode = self.mode_var.get()
        
        if mode == "Voegel":
            # Vogel-optimierte Einstellungen
            self.threshold_var.set(12)
            self.min_area_var.set(30)
            self.max_area_var.set(6000)
            self.min_movement_var.set(15)
            self.anti_cloud_min_area_var.set(50)
            self.anti_cloud_max_area_var.set(4000)
            self.min_speed_var.set(20)
            self.log("🐦 Vogel-Modus aktiviert - Parameter optimiert")
            
        elif mode == "Muecken":
            # Muecken-optimierte Einstellungen
            self.threshold_var.set(8)
            self.min_area_var.set(15)
            self.max_area_var.set(800)
            self.min_movement_var.set(8)
            self.anti_cloud_min_area_var.set(20)
            self.anti_cloud_max_area_var.set(600)
            self.min_speed_var.set(12)
            self.log("🦟 Muecken-Modus aktiviert - Parameter optimiert")
    
    def _toggle_tracking(self):
        """Toggle tracking on/off"""
        if not self.is_tracking:
            self._start_tracking()
        else:
            self._stop_tracking()
    
    def _start_tracking(self):
        """Start motion tracking mit maximaler Aufloesung"""
        try:
            # Cleanup vorherige Sessions
            self._cleanup_cameras()
            
            # Initialisiere Kameras mit MAXIMALER Aufloesung
            camera_count = 0
            for i in range(4):  # Teste bis zu 4 Kameras
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    # MAXIMALE Aufloesung setzen
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)   # Full HD Breite
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)  # Full HD Hoehe
                    cap.set(cv2.CAP_PROP_FPS, 30)            # 30 FPS
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)       # Minimaler Buffer
                    
                    # Teste ob Frame gelesen werden kann
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        actual_fps = cap.get(cv2.CAP_PROP_FPS)
                        
                        camera_name = f'webcam_{i}'
                        self.caps[camera_name] = cap
                        self.bg_subtractors[camera_name] = cv2.createBackgroundSubtractorMOG2(
                            history=300, varThreshold=16, detectShadows=False)
                        self.camera_motion_data[camera_name] = deque(maxlen=50)
                        
                        camera_count += 1
                        self.log(f"✅ {camera_name}: {actual_width}x{actual_height} @ {actual_fps:.1f}FPS")
                    else:
                        cap.release()
                else:
                    cap.release()
            
            if camera_count == 0:
                raise Exception("Keine Kameras gefunden!")
            
            self.is_tracking = True
            self.start_button.config(text="⏹️ Stop Tracking")
            self.status_var.set(f"🚀 Tracking aktiv - {camera_count} Kamera(s) mit maximaler Aufloesung")
            
            # Start tracking thread
            self.tracking_thread = threading.Thread(target=self._tracking_loop, daemon=True)
            self.tracking_thread.start()
            
            self.log(f"🚀 Tracking gestartet mit {camera_count} Kamera(s)")
            
        except Exception as e:
            self.log(f"❌ Fehler beim Starten: {str(e)}")
            self._cleanup_cameras()
    
    def _stop_tracking(self):
        """Stop motion tracking"""
        self.is_tracking = False
        self.start_button.config(text="🚀 Start Tracking")
        self.status_var.set("⏹️ Tracking gestoppt")
        
        self._cleanup_cameras()
        cv2.destroyAllWindows()
        
        self.log("⏹️ Tracking gestoppt")
    
    def _cleanup_cameras(self):
        """Cleanup camera resources"""
        for cap in self.caps.values():
            if cap.isOpened():
                cap.release()
        self.caps.clear()
        self.bg_subtractors.clear()
    
    def _tracking_loop(self):
        """Haupt-Tracking-Loop - PERFORMANCE OPTIMIERT"""
        frame_count = 0
        start_time = time.time()
        
        while self.is_tracking:
            try:
                frames = {}
                motion_counts = {}
                
                # Lese Frames von allen Kameras PARALLEL
                for camera_name, cap in self.caps.items():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        # Frame-Skip fuer Performance (nur wenn noetig)
                        self.current_frame_count += 1
                        if self.current_frame_count % self.frame_skip == 0:
                            # Verarbeite Frame
                            processed_frame, motion_count = self._process_motion(
                                frame, camera_name,
                                self.threshold_var.get(),
                                self.min_area_var.get(),
                                self.max_area_var.get()
                            )
                            frames[camera_name] = processed_frame
                            motion_counts[camera_name] = motion_count
                
                # Zeige Frames an (optimiert)
                if frames:
                    self._display_frames(frames, motion_counts, frame_count, start_time)
                    frame_count += 1
                
                # Kurze Pause fuer andere Threads
                time.sleep(0.02)  # ~50 FPS Maximum
                
            except Exception as e:
                self.log(f"⚠️ Tracking-Fehler: {str(e)}")
                time.sleep(0.1)
    
    def _process_motion(self, frame, camera_name, threshold, min_area, max_area):
        """Process motion detection auf Frame - OPTIMIERT"""
        if frame is None:
            return frame, 0
            
        bg_subtractor = self.bg_subtractors[camera_name]
        
        # Background subtraction
        fg_mask = bg_subtractor.apply(frame)
        
        # Apply threshold
        _, fg_mask = cv2.threshold(fg_mask, threshold, 255, cv2.THRESH_BINARY)
        
        # Morphological operations - OPTIMIERT
        kernel = np.ones((2,2), np.uint8)  # Kleinerer Kernel fuer Performance
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel, iterations=1)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel, iterations=1)
        
        # Find contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Process contours mit ANTI-WOLKEN FILTER
        motion_count = 0
        filtered_motion_count = 0
        result_frame = frame.copy()
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
                
                # ANTI-WOLKEN FILTER
                passes_filter = True
                filter_reasons = []
                
                # 1. Mindest-Bewegung
                min_movement = self.min_movement_var.get()
                if camera_name in self.camera_motion_data and len(self.camera_motion_data[camera_name]) >= 2:
                    last_motion = list(self.camera_motion_data[camera_name])[-1]
                    last_x = last_motion.get('x', 0)
                    last_y = last_motion.get('y', 0)
                    distance = ((center_x - last_x)**2 + (center_y - last_y)**2)**0.5
                    
                    if distance < min_movement:
                        passes_filter = False
                        filter_reasons.append("SLOW")
                    else:
                        filter_reasons.append("FAST")
                
                # 2. Anti-Cloud Area Filter
                anti_cloud_min = self.anti_cloud_min_area_var.get()
                anti_cloud_max = self.anti_cloud_max_area_var.get()
                
                if area < anti_cloud_min:
                    passes_filter = False
                    filter_reasons.append("TINY")
                elif area > anti_cloud_max:
                    passes_filter = False 
                    filter_reasons.append("HUGE")
                else:
                    filter_reasons.append("SIZE_OK")
                
                # 3. Speed Filter
                min_speed = self.min_speed_var.get()
                if camera_name in self.camera_motion_data and len(self.camera_motion_data[camera_name]) >= 3:
                    motions = list(self.camera_motion_data[camera_name])[-3:]
                    if len(motions) >= 2:
                        time_diff = motions[-1]['timestamp'] - motions[-2]['timestamp']
                        if time_diff > 0:
                            speed = distance / time_diff
                            speed_per_frame = speed / 30
                            
                            if speed_per_frame < min_speed:
                                passes_filter = False
                                filter_reasons.append("CRAWL")
                            else:
                                filter_reasons.append("BIRD_SPEED")
                
                # Filter result
                if not filter_reasons:
                    filter_reasons = ["FIRST"]
                    
                filter_reason = " ".join(filter_reasons[:2])
                
                # Draw based on filter result
                if passes_filter:
                    filtered_motion_count += 1
                    # Green = passes filter
                    cv2.rectangle(result_frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
                    cv2.putText(result_frame, f'F{filtered_motion_count}', 
                               (x, y-25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    cv2.putText(result_frame, filter_reason, 
                               (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
                    
                    # Store for Last Detection Window
                    padding = 40
                    detection_region = frame[max(0, y-padding):min(frame.shape[0], y+h+padding), 
                                           max(0, x-padding):min(frame.shape[1], x+w+padding)]
                    if detection_region.size > 0:
                        self.last_detection_frame = detection_region.copy()
                        self.last_detection_info = {
                            'timestamp': timestamp,
                            'camera': camera_name,
                            'area': area,
                            'center': (center_x, center_y),
                            'bbox': (x, y, w, h),
                            'reason': filter_reason,
                            'mode': self.mode_var.get()
                        }
                else:
                    # Red = filtered out
                    cv2.rectangle(result_frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                    cv2.putText(result_frame, f'M{motion_count}', 
                               (x, y-25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                    cv2.putText(result_frame, filter_reason, 
                               (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)
                
                # Motion data fuer 3D viewer (nur filtered)
                if passes_filter:
                    if camera_name not in self.camera_motion_data:
                        self.camera_motion_data[camera_name] = deque(maxlen=30)
                    self.camera_motion_data[camera_name].append({
                        'x': center_x,
                        'y': center_y, 
                        'area': area,
                        'timestamp': timestamp,
                        'camera': camera_name
                    })
        
        # Add stream info
        timestamp_str = datetime.now().strftime("%H:%M:%S")
        cv2.putText(result_frame, f'{camera_name} - {timestamp_str}', 
                   (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(result_frame, f'Motion: {motion_count} | Gefiltert: {filtered_motion_count}', 
                   (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        # Filter info
        mode = self.mode_var.get()
        cv2.putText(result_frame, f'{mode}-Modus | Anti-Wolken aktiv', 
                   (10, 105), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                   
        return result_frame, filtered_motion_count
        
    def _display_frames(self, frames, motion_counts, frame_count, start_time):
        """Display processed frames - OPTIMIERT fuer grosse Vorschau"""
        try:
            fps = frame_count / (time.time() - start_time + 0.001)
            
            if len(frames) == 1:
                # Single frame display - GROESSERE Vorschau
                name, frame = list(frames.items())[0]
                
                # Skaliere Frame fuer groessere Anzeige
                scale_factor = 1.2  # 20% groesser
                height, width = frame.shape[:2]
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                scaled_frame = cv2.resize(frame, (new_width, new_height))
                
                cv2.putText(scaled_frame, f'FPS: {fps:.1f}', 
                           (10, new_height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                cv2.imshow(f'Bird & Mosquito Tracker - {name}', scaled_frame)
                
            elif len(frames) == 2:
                # Dual frame display - nebeneinander, groesser
                names = list(frames.keys())
                frame1, frame2 = frames[names[0]], frames[names[1]]
                
                # Skaliere beide Frames
                scale_factor = 1.1  # 10% groesser
                height, width = frame1.shape[:2]
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                
                scaled_frame1 = cv2.resize(frame1, (new_width, new_height))
                scaled_frame2 = cv2.resize(frame2, (new_width, new_height))
                
                # Kombiniere horizontal
                combined = np.hstack([scaled_frame1, scaled_frame2])
                
                cv2.putText(combined, f'FPS: {fps:.1f}', 
                           (10, new_height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                cv2.imshow('Bird & Mosquito Tracker - Dual View', combined)
            
            # ESC zum Beenden
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                self._stop_tracking()
                
        except Exception as e:
            print(f"Display error: {e}")
    
    def _open_triangulation(self):
        """Oeffne 3D-Triangulation"""
        if not self.is_tracking:
            messagebox.showwarning("Triangulation", "Bitte starten Sie zuerst das Tracking!")
            return
            
        triangulation = Stable3DTriangulation(self)
        
        def start_triangulation():
            triangulation.start_triangulation()
            
        threading.Thread(target=start_triangulation, daemon=True).start()
        self.log("🚀 3D-Triangulation gestartet")
    
    def _show_last_detection(self):
        """Zeige letzte Erkennung"""
        if self.last_detection_frame is not None and self.last_detection_info is not None:
            info = self.last_detection_info
            
            # Skaliere fuer groessere Anzeige
            scale_factor = 3.0  # 3x groesser
            height, width = self.last_detection_frame.shape[:2]
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            scaled_frame = cv2.resize(self.last_detection_frame, (new_width, new_height), 
                                    interpolation=cv2.INTER_CUBIC)
            
            # Info overlay
            time_str = datetime.fromtimestamp(info['timestamp']).strftime("%H:%M:%S")
            cv2.putText(scaled_frame, f"Last Detection - {info['mode']} Mode", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
            cv2.putText(scaled_frame, f"Time: {time_str} | Area: {info['area']}px", 
                       (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(scaled_frame, f"Camera: {info['camera']} | Reason: {info['reason']}", 
                       (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            
            cv2.imshow("Last Detection - Enhanced View", scaled_frame)
        else:
            messagebox.showinfo("Last Detection", "Noch keine Erkennung verfuegbar!")
    
    def log(self, message):
        """Log message mit Timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, full_message)
        self.log_text.see(tk.END)
        print(full_message.strip())  # Auch in Konsole
    
    def run(self):
        """Start die Anwendung"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
            self.root.mainloop()
        except KeyboardInterrupt:
            self._on_closing()
    
    def _on_closing(self):
        """Sauberes Beenden"""
        if self.is_tracking:
            self._stop_tracking()
        self.root.destroy()


if __name__ == "__main__":
    print("🚀 Starte Bird & Mosquito Tracker...")
    app = BirdMosquitoTracker()
    app.run()
