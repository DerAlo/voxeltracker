#!/usr/bin/env python3
"""
STABILE 3D-TRIANGULATION - Optimiert und Vereinfacht
=====================================================
Crash-sichere 3D-Visualisierung mit matplotlib
Speziell fuer Bird & Mosquito Tracker optimiert
Alle Sonderzeichen kompatibel, Performance optimiert
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import time
import threading
from collections import deque

class Stable3DTriangulation:
    """Crash-sichere 3D Triangulation mit matplotlib - OPTIMIERT"""
    
    def __init__(self, tracker):
        self.tracker = tracker
        self.is_active = False
        self.fig = None
        self.ax = None
        self.zoom_level = 1.0
        
        # Kamera-Setup - VEREINFACHT
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
            print("Warnung: Triangulation laeuft bereits!")
            return
            
        print("Starte STABILE 3D-Triangulation (matplotlib)...")
        self.is_active = True
        
        # Erstelle matplotlib 3D-Plot - GROESSER
        plt.style.use('dark_background')
        self.fig = plt.figure(figsize=(16, 12))  # Noch groesser
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        # Setup 3D-Szene
        self._setup_3d_scene()
        
        # Zoom-Steuerung
        self._setup_zoom_controls()
        
        # Timer fuer Live-Updates - OPTIMIERT
        self.timer = self.fig.canvas.new_timer(interval=300)  # 3.3 FPS
        self.timer.add_callback(self._update_visualization)
        self.timer.start()
        
        # Window-Event fuer sauberes Schliessen
        self.fig.canvas.mpl_connect('close_event', self._on_close)
        
        plt.show()
        
    def _setup_zoom_controls(self):
        """Setup Zoom-Steuerung mit Mausrad"""
        def on_scroll(event):
            if event.inaxes != self.ax:
                return
                
            # Zoom-Faktor bestimmen
            zoom_factor = 1.3 if event.button == 'up' else 1/1.3
            
            # Schneller Zoom mit Strg
            if event.key == 'control':
                zoom_factor = zoom_factor ** 1.5
                
            # Zoom-Level anpassen
            self.zoom_level *= zoom_factor
            self.zoom_level = max(0.1, min(20.0, self.zoom_level))
            
            # Szene neu zeichnen
            self._setup_3d_scene()
            self.fig.canvas.draw()
            
        # Event-Handler verbinden
        self.fig.canvas.mpl_connect('scroll_event', on_scroll)
        
        # Tastatur-Shortcuts
        def on_key(event):
            if event.key == '+' or event.key == '=':
                self.zoom_level *= 1.3
                self._setup_3d_scene()
                self.fig.canvas.draw()
            elif event.key == '-':
                self.zoom_level /= 1.3
                self._setup_3d_scene()
                self.fig.canvas.draw()
            elif event.key == '0':
                self.zoom_level = 1.0
                self._setup_3d_scene()
                self.fig.canvas.draw()
                
        self.fig.canvas.mpl_connect('key_press_event', on_key)
        
    def _setup_3d_scene(self):
        """Setup 3D-Szene mit Kameras und Koordinatensystem - OPTIMIERT"""
        self.ax.clear()
        self.ax.set_facecolor('black')
        
        # Titel - VEREINFACHT
        self.ax.set_title('STABILE TRIANGULATION - Bird & Mosquito Tracking\n'
                         'Crash-sicher | Sync-Filter aktiv | Zoom mit Mausrad', 
                         color='cyan', fontsize=16, pad=30)
        
        # Achsen-Setup
        self.ax.set_xlabel('X (m)', color='red', fontsize=14)
        self.ax.set_ylabel('Y (m)', color='green', fontsize=14)  
        self.ax.set_zlabel('Z (m)', color='blue', fontsize=14)
        
        # Zoom-abhaengige Achsen-Limits
        base_limit = 3.0 / self.zoom_level
        self.ax.set_xlim([-base_limit, base_limit])
        self.ax.set_ylim([-base_limit/2, base_limit*2.5])
        self.ax.set_zlim([-base_limit/2, base_limit*2.5])
        
        # Koordinatenachsen zeichnen - GROESSER
        axis_length = base_limit * 0.8
        
        # X-Achse (rot)
        self.ax.plot([0, axis_length], [0, 0], [0, 0], 'r-', linewidth=5, alpha=0.9)
        self.ax.text(axis_length*1.1, 0, 0, 'X', color='red', fontsize=14, weight='bold')
        
        # Y-Achse (gruen)
        self.ax.plot([0, 0], [0, axis_length], [0, 0], 'g-', linewidth=5, alpha=0.9)
        self.ax.text(0, axis_length*1.1, 0, 'Y', color='green', fontsize=14, weight='bold')
        
        # Z-Achse (blau)
        self.ax.plot([0, 0], [0, 0], [0, axis_length], 'b-', linewidth=5, alpha=0.9)
        self.ax.text(0, 0, axis_length*1.1, 'Z', color='blue', fontsize=14, weight='bold')
        
        # Boden-Grid - ADAPTIVE GROESSE
        grid_range = base_limit
        xx, yy = np.meshgrid(np.linspace(-grid_range, grid_range, 7), 
                            np.linspace(-grid_range/2, grid_range*2.5, 9))
        zz = np.zeros_like(xx) - 0.3/self.zoom_level
        self.ax.plot_wireframe(xx, yy, zz, alpha=0.3, color='gray')
        
        # Zeichne Kameras - VERBESSERT
        for camera_name, position in self.camera_positions.items():
            if hasattr(self.tracker, 'caps') and camera_name in self.tracker.caps:
                color = self.camera_colors.get(camera_name, 'white')
                
                # Kamera als groesseren, markanten Punkt
                self.ax.scatter(*position, color=color, s=300, alpha=1.0, 
                              marker='s', edgecolors='white', linewidth=3)
                
                # Kamera-Label - GROESSER
                self.ax.text(position[0], position[1], position[2] + 0.15/self.zoom_level, 
                           camera_name.replace('webcam_', 'KAMERA '), 
                           color='white', fontsize=12, weight='bold',
                           bbox={'boxstyle': "round,pad=0.4", 'facecolor': color, 'alpha': 0.8})
                
                # Verbesserte Sichtfeld-Visualisierung
                self._draw_enhanced_camera_fov(position, color)
                
                # Kamera-Orientierungspfeil
                self._draw_camera_orientation(position, color)
        
        # Info-Box - VEREINFACHT und OHNE SONDERZEICHEN
        info_text = ("SYNC-FILTER AKTIV:\n"
                    "- Nur zeitgleiche Bewegungen (+-200ms)\n" 
                    "- Beide Kameras muessen Motion erkennen\n"
                    "- Optimiert fuer Voegel und Muecken\n\n"
                    "STEUERUNG:\n"
                    "- Maus-Drag: 3D-Rotation\n"
                    "- Mausrad: Zoom In/Out\n"
                    "- Strg+Mausrad: Schneller Zoom\n"
                    "- Tasten +/-: Zoom, 0: Reset\n"
                    "- Rechts-Drag: Pan-Bewegung\n\n"
                    "KAMERA-SETUP:\n"
                    "- ROT: Linke Kamera (5cm links)\n"
                    "- GRUEN: Rechte Kamera (5cm rechts)\n"
                    "- Weisse Pfeile: Orientierung\n"
                    "- Kegel: Sichtfeld\n\n"
                    "STABIL-MODUS:\n"
                    "- matplotlib statt PyVista\n"
                    "- Maximale Aufloesung\n"
                    "- Timer-basierte Updates\n"
                    "- Crash-sicher!")
                    
        self.ax.text2D(0.02, 0.98, info_text, transform=self.ax.transAxes,
                      fontsize=9, color='yellow', verticalalignment='top',
                      bbox={'boxstyle': "round,pad=0.5", 'facecolor': 'black', 
                           'alpha': 0.9, 'edgecolor': 'yellow'})
        
    def _draw_enhanced_camera_fov(self, position, color):
        """Zeichne verbessertes Sichtfeld-Kegel fuer Kamera"""
        # Tracking-Richtung
        direction = np.array([0, 0.7, 0.7])  # 45 Grad nach oben
        fov_distance = 4.0 / self.zoom_level  # Zoom-angepasst
        fov_angle = 60  # Grad
        
        # Kegel-Endpunkt
        end_point = position + direction * fov_distance
        
        # Hauptsichtstrahl - DICKER
        self.ax.plot([position[0], end_point[0]],
                    [position[1], end_point[1]], 
                    [position[2], end_point[2]], 
                    color=color, alpha=0.8, linewidth=5)
        
        # Sichtfeld-Kegel als Pyramide
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
                        color=color, alpha=0.4, linewidth=2)
                        
    def _draw_camera_orientation(self, position, color):
        """Zeichne Orientierungspfeil fuer bessere Kamera-Identifikation"""
        # Orientierungspfeil nach oben
        arrow_length = 0.3 / self.zoom_level
        arrow_end = position + np.array([0, 0, arrow_length])
        
        self.ax.plot([position[0], arrow_end[0]],
                    [position[1], arrow_end[1]], 
                    [position[2], arrow_end[2]], 
                    color='white', alpha=1.0, linewidth=4)
                    
        # Pfeilspitze
        self.ax.scatter(*arrow_end, color='white', s=80, marker='^', alpha=1.0)
    
    def _update_visualization(self):
        """Live-Update der Visualization - THREAD-SICHER und OPTIMIERT"""
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
            print(f"Update-Fehler (ignoriert): {str(e)[:50]}...")
            
    def _filter_synchronized_motions(self):
        """Filtere nur zeitgleiche Bewegungen - OPTIMIERT"""
        try:
            if not hasattr(self.tracker, 'camera_motion_data') or \
               len(self.tracker.camera_motion_data) < 2:
                return {}
                
            current_time = time.time()
            sync_tolerance = 0.2  # 200ms Toleranz - SCHNELLER
            
            # Sammle aktuelle Motion-Events
            recent_motions = {}
            for camera_name, motion_list in self.tracker.camera_motion_data.items():
                if camera_name not in self.camera_positions or not motion_list:
                    continue
                    
                # Nur Events der letzten Sekunde
                very_recent = []
                for motion in motion_list:
                    try:
                        if current_time - motion['timestamp'] < 0.8:  # Kuerzer
                            very_recent.append(motion)
                    except Exception:
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
                            except Exception:
                                continue
            
            return best_match or {}
            
        except Exception:
            return {}
    
    def _clear_motion_objects(self):
        """Entferne alte Motion-Objekte"""
        # matplotlib: Einfach Scene neu aufbauen
        self._setup_3d_scene()
        
    def _draw_filtered_rays(self, synchronized_motions):
        """Zeichne gefilterte Camera Rays - OPTIMIERT"""
        try:
            for camera_name, motion in synchronized_motions.items():
                if camera_name not in self.camera_positions:
                    continue
                    
                camera_pos = self.camera_positions[camera_name]
                camera_color = self.camera_colors.get(camera_name, 'white')
                
                # 3D Richtung berechnen
                direction = self._pixel_to_3d_direction(motion['x'], motion['y'])
                
                # Strahl fuer Tracking
                ray_length = 5.0 / self.zoom_level  # Zoom-angepasst
                ray_end = camera_pos + direction * ray_length
                
                # Strahl zeichnen - DICKER
                self.ax.plot([camera_pos[0], ray_end[0]],
                           [camera_pos[1], ray_end[1]], 
                           [camera_pos[2], ray_end[2]], 
                           color=camera_color, linewidth=4, alpha=0.9)
                
                # Motion-Punkt markieren - GROESSER
                self.ax.scatter(*ray_end, color=camera_color, s=120, alpha=1.0)
                
        except Exception:
            pass
    
    def _calculate_and_draw_triangulation(self, synchronized_motions):
        """Berechne und zeichne Triangulation - OPTIMIERT"""
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
                        dir1 = self._pixel_to_3d_direction(motion1['x'], motion1['y'])
                        
                        pos2 = self.camera_positions[cam2_name]
                        dir2 = self._pixel_to_3d_direction(motion2['x'], motion2['y'])
                        
                        # Triangulation
                        intersection, confidence = self._line_intersection_3d_with_confidence(pos1, dir1, pos2, dir2)
                        
                        if intersection is not None and confidence > 0.25:  # Weniger restriktiv
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
                    self.ax.scatter(*weighted_position, color='cyan', s=300, alpha=1.0, 
                                  marker='o', edgecolors='white', linewidth=3)
                    
                    # Koordinaten-Info - OHNE SONDERZEICHEN
                    distance = np.linalg.norm(weighted_position)
                    if distance > 0.8:  # Nur bei realistischen Entfernungen
                        coord_text = f"Position: {distance:.1f}m\n({weighted_position[0]:.1f}, {weighted_position[1]:.1f}, {weighted_position[2]:.1f})"
                        self.ax.text(weighted_position[0], weighted_position[1], weighted_position[2] + 0.3,
                                   coord_text, color='cyan', fontsize=11, ha='center', weight='bold')
                    
        except Exception:
            pass
    
    def _pixel_to_3d_direction(self, pixel_x, pixel_y):
        """Konvertiere 2D Pixel zu 3D Richtung - OPTIMIERT fuer hohe Aufloesung"""
        # Normalisiere Pixel-Koordinaten fuer Full HD
        norm_x = (pixel_x - 960) / 960  # 1920x1080
        norm_y = (pixel_y - 540) / 540
        
        # FOV-Faktor
        fov_factor = 0.8  # 70 Grad FOV
        
        # Tracking: Beide Kameras parallel nach oben/vorne
        base_dir = np.array([0, 0.7, 0.7])  # 45 Grad nach oben
        right_vec = np.array([1, 0, 0])
        up_vec = np.array([0, 0.7, -0.7])
        
        # Richtung berechnen
        direction = base_dir + (right_vec * norm_x * fov_factor) + (up_vec * norm_y * fov_factor)
        
        return direction / np.linalg.norm(direction)
    
    def _line_intersection_3d_with_confidence(self, p1, d1, p2, d2):
        """3D Linien-Intersection mit Confidence - OPTIMIERT"""
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
        
        # Confidence fuer grosse Entfernungen - ANGEPASST
        distance = np.linalg.norm(closest1 - closest2)
        confidence = max(0.0, 1.0 - distance / 6.0)  # 6m Toleranz
        
        return intersection, confidence
    
    def _on_close(self, event):
        """Sauberes Schliessen"""
        print("Stabile Triangulation beendet")
        self.is_active = False
        if hasattr(self, 'timer'):
            self.timer.stop()


if __name__ == "__main__":
    print("Stabile 3D-Triangulation geladen")
    print("Verwenden Sie: triangulation = Stable3DTriangulation(tracker)")
    print("Dann: triangulation.start_triangulation()")
        
    def start_triangulation(self):
        """Starte stabile 3D-Triangulation"""
        if self.is_active:
            print("⚠️ Triangulation läuft bereits!")
            return
            
        print("🚀 Starte STABILE 3D-Triangulation (matplotlib)...")
        self.is_active = True
        
        # Erstelle matplotlib 3D-Plot
        plt.style.use('dark_background')
        self.fig = plt.figure(figsize=(12, 8))
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        # Setup 3D-Szene
        self._setup_3d_scene()
        
        # Timer für Live-Updates  
        self.timer = self.fig.canvas.new_timer(interval=500)  # 2 FPS
        self.timer.add_callback(self._update_visualization)
        self.timer.start()
        
        # Window-Event für sauberes Schließen
        self.fig.canvas.mpl_connect('close_event', self._on_close)
        
        plt.show()
        
    def _setup_3d_scene(self):
        """Setup 3D-Szene mit Kameras und Koordinatensystem"""
        self.ax.clear()
        self.ax.set_facecolor('black')
        
        # Titel
        self.ax.set_title('🎯 STABILE TRIANGULATION - Himmel Tracking\n'
                         '✅ Crash-sicher | 🔄 Sync-Filter aktiv', 
                         color='cyan', fontsize=12, pad=20)
        
        # Achsen-Setup
        self.ax.set_xlabel('X (m)', color='red')
        self.ax.set_ylabel('Y (m)', color='green')  
        self.ax.set_zlabel('Z (m)', color='blue')
        
        # Achsen-Limits für Himmel-Tracking
        self.ax.set_xlim([-2, 2])
        self.ax.set_ylim([-1, 5])
        self.ax.set_zlim([-1, 5])
        
        # Koordinatenachsen zeichnen
        origin = [0, 0, 0]
        
        # X-Achse (rot)
        self.ax.plot([0, 2], [0, 0], [0, 0], 'r-', linewidth=3, alpha=0.7)
        self.ax.text(2.2, 0, 0, 'X', color='red', fontsize=10)
        
        # Y-Achse (grün)
        self.ax.plot([0, 0], [0, 2], [0, 0], 'g-', linewidth=3, alpha=0.7)
        self.ax.text(0, 2.2, 0, 'Y', color='green', fontsize=10)
        
        # Z-Achse (blau)
        self.ax.plot([0, 0], [0, 0], [0, 2], 'b-', linewidth=3, alpha=0.7)
        self.ax.text(0, 0, 2.2, 'Z', color='blue', fontsize=10)
        
        # Boden-Grid
        xx, yy = np.meshgrid(np.linspace(-2, 2, 5), np.linspace(-1, 5, 7))
        zz = np.zeros_like(xx) - 0.5
        self.ax.plot_wireframe(xx, yy, zz, alpha=0.2, color='gray')
        
        # Zeichne Kameras
        for camera_name, position in self.camera_positions.items():
            if camera_name in getattr(self.master_tracker, 'caps', {}):
                color = self.camera_colors.get(camera_name, 'white')
                
                # Kamera als Punkt
                self.ax.scatter(*position, color=color, s=100, alpha=0.8)
                
                # Kamera-Label
                self.ax.text(position[0], position[1], position[2] + 0.1, 
                           camera_name, color=color, fontsize=8)
                
                # Sichtfeld-Kegel (vereinfacht)
                self._draw_camera_fov(position, color)
        
        # Info-Text
        info_text = ("📍 SYNC-FILTER AKTIV:\n"
                    "• Nur zeitgleiche Bewegungen (±300ms)\n" 
                    "• Beide Kameras müssen Motion erkennen\n"
                    "• Himmel-Tracking: 100m Strahlen\n\n"
                    "⚠️ STABIL-MODUS:\n"
                    "• matplotlib statt PyVista\n"
                    "• Timer-basierte Updates\n"
                    "• Crash-sicher!")
                    
        self.ax.text2D(0.02, 0.98, info_text, transform=self.ax.transAxes,
                      fontsize=8, color='yellow', verticalalignment='top',
                      bbox=dict(boxstyle="round,pad=0.3", facecolor='black', alpha=0.7))
        
    def _draw_camera_fov(self, position, color):
        """Zeichne Sichtfeld-Kegel für Kamera"""
        # Himmel-Richtung (60° Elevation)
        direction = np.array([0, 0.5, 0.866])  # 60° nach oben
        fov_distance = 3.0  # Reduziert für bessere Sichtbarkeit
        
        # Kegel-Endpunkt
        end_point = position + direction * fov_distance
        
        # Einfacher Sichtstrahl
        self.ax.plot([position[0], end_point[0]],
                    [position[1], end_point[1]], 
                    [position[2], end_point[2]], 
                    color=color, alpha=0.3, linewidth=2)
        
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
        """Filtere nur zeitgleiche Bewegungen - identisch zur PyVista-Version"""
        try:
            if not hasattr(self.master_tracker, 'camera_motion_data') or \
               len(self.master_tracker.camera_motion_data) < 2:
                return {}
                
            current_time = time.time()
            sync_tolerance = 0.3  # 300ms Toleranz
            
            # Sammle aktuelle Motion-Events
            recent_motions = {}
            for camera_name, motion_list in self.master_tracker.camera_motion_data.items():
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
            
            # Finde beste zeitliche Übereinstimmung
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
                        
                        if intersection is not None and confidence > 0.2:
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
                    
                    # Finale Position als große Kugel
                    self.ax.scatter(*weighted_position, color='cyan', s=200, alpha=1.0, 
                                  marker='o', edgecolors='white', linewidth=2)
                    
                    # Koordinaten-Info
                    distance = np.linalg.norm(weighted_position)
                    if distance > 1:  # Nur bei realistischen Entfernungen
                        coord_text = f"📍 {distance:.1f}m\n({weighted_position[0]:.1f}, {weighted_position[1]:.1f}, {weighted_position[2]:.1f})"
                        self.ax.text(weighted_position[0], weighted_position[1], weighted_position[2] + 0.2,
                                   coord_text, color='cyan', fontsize=8, ha='center')
                    
        except Exception:
            pass
    
    def _pixel_to_3d_direction(self, pixel_x, pixel_y, camera_name):
        """Konvertiere 2D Pixel zu 3D Richtung - Himmel-Tracking"""
        # Normalisiere Pixel-Koordinaten
        norm_x = (pixel_x - 320) / 320  # Annahme: 640x480
        norm_y = (pixel_y - 240) / 240
        
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


# Integration in MasterMotionTracker
def add_stable_triangulation_to_master(master_tracker_class):
    """Füge stabile Triangulation zur Master-Klasse hinzu"""
    
    def open_stable_triangulation_view(self):
        """Öffne stabile 3D-Triangulation mit matplotlib"""
        if not self.is_tracking:
            from tkinter import messagebox
            messagebox.showwarning("Triangulation", "Bitte starten Sie zuerst das Motion Tracking!")
            return
            
        # Erstelle stabile Triangulation
        triangulation = Stable3DTriangulation(self)
        
        # Starte in separatem Thread
        def start_stable():
            triangulation.start_triangulation()
            
        threading.Thread(target=start_stable, daemon=True).start()
        self.log("🚀 Stabile 3D-Triangulation gestartet (matplotlib)")
    
    # Methode zur Klasse hinzufügen
    master_tracker_class.open_stable_triangulation_view = open_stable_triangulation_view


if __name__ == "__main__":
    print("🎯 Stabile 3D-Triangulation geladen")
    print("Verwenden Sie: triangulation = Stable3DTriangulation(master_tracker)")
    print("Dann: triangulation.start_triangulation()")
