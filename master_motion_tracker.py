#!/usr/bin/env python3
"""
🎯 Pixeltovoxelprojector - Master Motion Tracker
==============================================

Einheitliches GUI-System für alle Motion-Tracking-Modi:
- 🦟 Mücken-Tracking (lokale Webcam)  
- 🐦 Vogel-Tracking (lokale Webcam)
- ✈️ Flugzeug-Tracking (lokale Webcam)
- 🌊 Niagara Falls Demo (YouTube Live-Streams)
- 📺 Webcam-Investigation (öffentliche Webcams)

Alle Profile und Quellen in einem Tool!
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
import pyvista as pv

# OpenGL-Kompatibilitätskonfiguration für Windows
try:
    import os
    # Setze OpenGL-Environment für bessere Stabilität
    os.environ['PYVISTA_OFF_SCREEN'] = 'false'
    os.environ['PYVISTA_USE_PANEL'] = 'false'
    os.environ['VTK_SILENCE_GET_VOID_POINTER_WARNINGS'] = '1'
    
    # Teste PyVista OpenGL-Kompatibilität
    pv.set_plot_theme("dark")
    
    # Teste minimalen Plotter
    test_plotter = pv.Plotter(off_screen=True, window_size=[100, 100])
    test_plotter.close()
    
    PYVISTA_AVAILABLE = True
    print("✅ PyVista OpenGL-Test erfolgreich")
    
except Exception as pv_error:
    PYVISTA_AVAILABLE = False
    print(f"⚠️ PyVista OpenGL-Warnung: {pv_error}")
    print("📐 3D Triangulation wird im Fallback-Modus laufen")

# Detection Profiles für verschiedene Ziele
DETECTION_PROFILES = {
    "🦟 Mosquito": {
        "threshold": 15,
        "min_area": 10,
        "max_area": 150,
        "fps": 60,
        "resolution": (640, 480),
        "description": "Optimiert für kleine, schnelle Insekten"
    },
    "🐦 Bird": {
        "threshold": 30,
        "min_area": 200,
        "max_area": 5000,
        "fps": 30,
        "resolution": (800, 600),
        "description": "Optimiert für Vögel und mittlere Flugobjekte"
    },
    "✈️ Aircraft": {
        "threshold": 40,
        "min_area": 500,
        "max_area": 50000,
        "fps": 15,
        "resolution": (1280, 720),
        "description": "Optimiert für Flugzeuge und große Objekte"
    },
    "🎯 Custom": {
        "threshold": 25,
        "min_area": 100,
        "max_area": 10000,
        "fps": 30,
        "resolution": (640, 480),
        "description": "Manuelle Konfiguration"
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
        
        self.triangulation_btn = ttk.Button(control_frame, text="📐 3D Triangulation", 
                                           command=self.open_triangulation_view)
        self.triangulation_btn.pack(side=tk.LEFT, padx=5)
        
        # Advanced settings (collapsible)
        self.settings_visible = False
        self.settings_btn = ttk.Button(control_frame, text="⚙️ Advanced Settings", 
                                      command=self.toggle_settings)
        self.settings_btn.pack(side=tk.LEFT, padx=5)
        
        # Advanced settings frame (initially hidden)
        self.settings_frame = ttk.LabelFrame(self.root, text="🔧 Advanced Settings")
        
        # Threshold
        ttk.Label(self.settings_frame, text="🎯 Motion Threshold (Sensitivity):").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.threshold_var = tk.IntVar(value=25)
        threshold_scale = ttk.Scale(self.settings_frame, from_=5, to=100, 
                                   variable=self.threshold_var, orient=tk.HORIZONTAL, length=200)
        threshold_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        threshold_label = ttk.Label(self.settings_frame, textvariable=self.threshold_var)
        threshold_label.grid(row=0, column=2, padx=5)
        
        # Min area
        ttk.Label(self.settings_frame, text="📏 Min Object Size (pixels):").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.min_area_var = tk.IntVar(value=100)
        min_area_scale = ttk.Scale(self.settings_frame, from_=1, to=1000, 
                                  variable=self.min_area_var, orient=tk.HORIZONTAL, length=200)
        min_area_scale.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        min_area_label = ttk.Label(self.settings_frame, textvariable=self.min_area_var)
        min_area_label.grid(row=1, column=2, padx=5)
        
        # Max area
        ttk.Label(self.settings_frame, text="📐 Max Object Size (pixels):").grid(row=2, column=0, sticky=tk.W, padx=5)
        self.max_area_var = tk.IntVar(value=10000)
        max_area_scale = ttk.Scale(self.settings_frame, from_=100, to=50000, 
                                  variable=self.max_area_var, orient=tk.HORIZONTAL, length=200)
        max_area_scale.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)
        max_area_label = ttk.Label(self.settings_frame, textvariable=self.max_area_var)
        max_area_label.grid(row=2, column=2, padx=5)
        
        # Help text
        help_text = "💡 Tipp: Niedrigere Threshold = höhere Sensitivität. Größere Min Area = weniger Rauschen."
        ttk.Label(self.settings_frame, text=help_text, font=("Arial", 8), foreground="gray").grid(
            row=3, column=0, columnspan=3, sticky=tk.W, padx=5, pady=(5,0))
        
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
        """Öffne die Live 3D Camera Triangulation View mit OpenGL-Fehlerbehandlung"""
        # Verhindere Mehrfachklicks
        if hasattr(self, 'triangulation_starting') and self.triangulation_starting:
            self.log("⚠️ Triangulation startet bereits, bitte warten...")
            return
            
        if hasattr(self, 'triangulation_active') and self.triangulation_active:
            messagebox.showinfo("Triangulation", "3D Triangulation View läuft bereits!")
            return
            
        if not self.is_tracking:
            messagebox.showwarning("Triangulation", "Bitte starten Sie zuerst das Motion Tracking!")
            return
        
        # Setze Starting-Flag
        self.triangulation_starting = True
        self.log("🚀 Starte 3D Triangulation...")
        
        # Prüfe PyVista-Verfügbarkeit
        if not PYVISTA_AVAILABLE:
            self.triangulation_starting = False
            messagebox.showerror("3D Triangulation", 
                               "PyVista 3D-Rendering nicht verfügbar!\n\n"
                               "Mögliche Lösungen:\n"
                               "• Grafiktreiber aktualisieren\n"
                               "• pip install --upgrade pyvista\n"
                               "• Neustart des Systems")
            self.triangulation_starting = False
            return
            
        # Beende vorherigen Thread falls aktiv
        if hasattr(self, 'triangulation_thread'):
            try:
                if self.triangulation_thread.is_alive():
                    self.triangulation_active = False
                    self.triangulation_thread.join(timeout=2.0)  # Warte max 2 Sekunden
            except Exception as e:
                self.log(f"⚠️ Thread-Cleanup-Fehler: {e}")
            
            # Entferne die Thread-Referenz komplett
            delattr(self, 'triangulation_thread')
        
        self.triangulation_active = True
        
        # Erstelle neuen Thread (Threads können nur einmal gestartet werden)
        self.triangulation_thread = threading.Thread(target=self._triangulation_worker, daemon=True)
        self.triangulation_thread.start()
        
        # Reset Starting-Flag
        self.triangulation_starting = False
        
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
                
                # Robuste OpenGL-Initialisierung
                try:
                    plotter = pv.Plotter(title="🎯 LIVE 3D Triangulation - Mosquito & Object Tracking",
                                       window_size=[1200, 800])  # Entferne multi_samples
                    plotter.background_color = 'black'
                except Exception as plotter_error:
                    # Fallback: Noch einfacherer Plotter
                    self.log(f"⚠️ Standard Plotter fehlgeschlagen: {plotter_error}")
                    plotter = pv.Plotter(window_size=[1000, 700])
                    plotter.background_color = 'black'
                
                # Sicherer Anti-Aliasing-Test
                try:
                    plotter.enable_anti_aliasing()
                except Exception:
                    pass  # Fallback wenn nicht unterstützt
                    
                # Depth peeling nur wenn unterstützt
                try:
                    if hasattr(plotter, 'enable_depth_peeling'):
                        plotter.enable_depth_peeling()
                except Exception:
                    pass  # Fallback
                    
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
            
            # Steuerungstext
            plotter.add_text("🎯 LIVE 3D TRIANGULATION\n\n"
                            "📷 Kamera-Positionen (realistisch):\n"
                            "• Webcam 0: ROT (Links, -1m)\n"
                            "• Webcam 1: GRÜN (Rechts, +1m)\n" 
                            "• Webcam 2: BLAU (Zentrum)\n\n"
                            "🔄 Physische Anordnung:\n"
                            "• Nebeneinander auf gleicher Höhe\n"
                            "• 30° Rotation zueinander\n"
                            "• Überlappende Sichtfelder\n\n"
                            "🦟 LIVE TRACKING:\n"
                            "• Orange Strahlen: Motion Detection\n"
                            "• Cyan Kugel: Trianguliertes Objekt\n"
                            "• Koordinaten werden live aktualisiert\n\n"
                            "🎮 Steuerung:\n"
                            "• Maus-Drag: 3D Navigation\n"
                            "• Rad: Zoom\n"
                            "• R: Reset View\n"
                            "• Q: Beenden", 
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
        """Führe Live-Updates ohne plotter.show() aus um Thread-Konflikte zu vermeiden"""
        try:
            # Show the plotter window once
            plotter.show(interactive=False, auto_close=False)
            
            # Run live update loop
            update_counter = 0
            error_count = 0
            max_errors = 10
            
            while self.triangulation_active and self.is_tracking and error_count < max_errors:
                try:
                    # Robuste Render-Zyklen mit Fehlerbehandlung
                    if update_counter % 5 == 0:  # Weniger häufige komplette Updates
                        self._clear_motion_objects(plotter)
                    
                    if self.camera_motion_data:
                        self._draw_live_camera_rays(plotter)
                        self._calculate_live_triangulation(plotter)
                    
                    # Sehr konservative Render-Updates um OpenGL-Konflikte zu vermeiden
                    if update_counter % 3 == 0:  # Render nur alle 3 Frames
                        try:
                            plotter.render()
                            error_count = 0  # Reset error counter bei erfolgreichem Render
                        except Exception as render_error:
                            error_count += 1
                            self.log(f"⚠️ Render-Fehler {error_count}/{max_errors}: {render_error}")
                            if error_count >= max_errors:
                                self.log("❌ Zu viele Render-Fehler, stoppe Live-Updates")
                                break
                    
                    update_counter += 1
                    time.sleep(0.2)  # Längere Pause für stabileres Rendering (5 FPS)
                    
                except Exception as e:
                    error_count += 1
                    self.log(f"⚠️ Live update error {error_count}/{max_errors}: {e}")
                    time.sleep(1.0)  # Längere Pause bei Fehlern
                    if error_count >= max_errors:
                        self.log("❌ Zu viele Update-Fehler, stoppe Live-Updates")
                        break
                        
        except Exception as e:
            self.log(f"❌ Live-Updates fehlgeschlagen: {e}")
            
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
        fov_distance = 3.0  # 3 Meter Sichtweite
        
        # Berechne Kegel-Richtung basierend auf physische Anordnung
        # Beide Kameras schauen nach vorne, aber um 30° zueinander rotiert
        if camera_name == 'webcam_0':
            direction = np.array([0.5, 0.866, 0])  # 30° nach rechts (von links kommend)
        elif camera_name == 'webcam_1':
            direction = np.array([-0.5, 0.866, 0])  # 30° nach links (von rechts kommend)
        elif camera_name == 'webcam_2':
            direction = np.array([0, 1, 0])  # Zentral nach vorne (falls vorhanden)
        else:
            direction = np.array([0, 1, 0])  # Default nach vorne
        
        # Erstelle Sichtfeld-Kegel
        cone_center = position + direction * (fov_distance / 2)
        fov_cone = pv.Cone(center=cone_center, direction=direction,
                          height=fov_distance, radius=fov_distance * np.tan(np.radians(fov_angle/2)),
                          resolution=8)
        
        # Füge transparenten Sichtfeld-Kegel hinzu
        plotter.add_mesh(fov_cone, color=color, opacity=0.2, style='wireframe')
                
    def _setup_camera_controls(self, plotter):
        """Setup interaktive Kamera-Positionierungs-Controls"""
        # Checkbox für jede Kamera für einfache Positionierung
        control_text = ("📍 KAMERA-POSITIONIERUNG:\n"
                       "• Drag & Drop Kameras in 3D\n"
                       "• Rechtsklick: Kamera-Menü\n"
                       "• Realistische Anordnung:\n"
                       "  - Nebeneinander auf gleicher Höhe\n"
                       "  - 30° Rotation zueinander\n"
                       "  - Überlappende Sichtfelder\n\n"
                       "🎮 LIVE CONTROLS:\n"
                       "• 1-3: Kamera auswählen & bewegen\n"
                       "• X/Y/Z: Achse sperren\n"
                       "• R: Reset Positionen")
        
        plotter.add_text(control_text, position='lower_left', font_size=8, color='yellow')
        
        # Interaktive Kamera-Positionierung mit korrekter PyVista Callback-Syntax
        def on_key_1():
            """Kamera 1 auswählen"""
            self.selected_camera = 'webcam_0'
            self.log("📷 Kamera ausgewählt: webcam_0")
            
        def on_key_2():
            """Kamera 2 auswählen"""
            self.selected_camera = 'webcam_1'
            self.log("📷 Kamera ausgewählt: webcam_1")
            
        def on_key_3():
            """Kamera 3 auswählen"""
            self.selected_camera = 'webcam_2'
            self.log("📷 Kamera ausgewählt: webcam_2")
            
        def on_key_r():
            """Reset Kamera-Positionen"""
            self._reset_camera_positions()
            self.log("📍 Kamera-Positionen zurückgesetzt")
            
        def on_key_w():
            """Kamera vorwärts bewegen (Y+)"""
            if hasattr(self, 'selected_camera') and self.selected_camera:
                step = 0.5
                pos = self.camera_positions[self.selected_camera]
                self.camera_positions[self.selected_camera] = pos + np.array([0, step, 0])
                new_pos = self.camera_positions[self.selected_camera]
                self.log(f"📍 {self.selected_camera}: X={new_pos[0]:.1f}, Y={new_pos[1]:.1f}, Z={new_pos[2]:.1f}")
                
        def on_key_s():
            """Kamera rückwärts bewegen (Y-)"""
            if hasattr(self, 'selected_camera') and self.selected_camera:
                step = 0.5
                pos = self.camera_positions[self.selected_camera]
                self.camera_positions[self.selected_camera] = pos + np.array([0, -step, 0])
                new_pos = self.camera_positions[self.selected_camera]
                self.log(f"📍 {self.selected_camera}: X={new_pos[0]:.1f}, Y={new_pos[1]:.1f}, Z={new_pos[2]:.1f}")
                
        def on_key_a():
            """Kamera links bewegen (X-)"""
            if hasattr(self, 'selected_camera') and self.selected_camera:
                step = 0.5
                pos = self.camera_positions[self.selected_camera]
                self.camera_positions[self.selected_camera] = pos + np.array([-step, 0, 0])
                new_pos = self.camera_positions[self.selected_camera]
                self.log(f"📍 {self.selected_camera}: X={new_pos[0]:.1f}, Y={new_pos[1]:.1f}, Z={new_pos[2]:.1f}")
                
        def on_key_d():
            """Kamera rechts bewegen (X+)"""
            if hasattr(self, 'selected_camera') and self.selected_camera:
                step = 0.5
                pos = self.camera_positions[self.selected_camera]
                self.camera_positions[self.selected_camera] = pos + np.array([step, 0, 0])
                new_pos = self.camera_positions[self.selected_camera]
                self.log(f"📍 {self.selected_camera}: X={new_pos[0]:.1f}, Y={new_pos[1]:.1f}, Z={new_pos[2]:.1f}")
                
        def on_key_q():
            """Kamera hoch bewegen (Z+)"""
            if hasattr(self, 'selected_camera') and self.selected_camera:
                step = 0.5
                pos = self.camera_positions[self.selected_camera]
                self.camera_positions[self.selected_camera] = pos + np.array([0, 0, step])
                new_pos = self.camera_positions[self.selected_camera]
                self.log(f"📍 {self.selected_camera}: X={new_pos[0]:.1f}, Y={new_pos[1]:.1f}, Z={new_pos[2]:.1f}")
                
        def on_key_e():
            """Kamera runter bewegen (Z-)"""
            if hasattr(self, 'selected_camera') and self.selected_camera:
                step = 0.5
                pos = self.camera_positions[self.selected_camera]
                self.camera_positions[self.selected_camera] = pos + np.array([0, 0, -step])
                new_pos = self.camera_positions[self.selected_camera]
                self.log(f"📍 {self.selected_camera}: X={new_pos[0]:.1f}, Y={new_pos[1]:.1f}, Z={new_pos[2]:.1f}")
        
        # Keyboard callbacks hinzufügen (PyVista-kompatibel ohne Argumente)
        plotter.add_key_event('1', on_key_1)
        plotter.add_key_event('2', on_key_2)
        plotter.add_key_event('3', on_key_3)
        plotter.add_key_event('w', on_key_w)
        plotter.add_key_event('s', on_key_s)
        plotter.add_key_event('a', on_key_a)
        plotter.add_key_event('d', on_key_d)
        plotter.add_key_event('q', on_key_q)
        plotter.add_key_event('e', on_key_e)
        plotter.add_key_event('r', on_key_r)
    
    def _reset_camera_positions(self):
        """Reset Kamera-Positionen zu Standard-Werten - nebeneinander auf gleicher Höhe, 30° gedreht"""
        # Webcams nebeneinander auf gleicher Höhe, nur rotiert um 30° für überlappende Sichtfelder
        self.camera_positions = {
            'webcam_0': np.array([-1, 0, 0]),     # Links (1m von Zentrum)
            'webcam_1': np.array([1, 0, 0]),      # Rechts (1m von Zentrum)
            'webcam_2': np.array([0, 0, 0])       # Zentrum (falls 3. Kamera vorhanden)
        }
    
    def _clear_motion_objects(self, plotter):
        """Entferne nur motion-relevante Objekte für Live-Updates"""
        # Suche und entferne nur temporäre Tracking-Objekte
        actors_to_remove = []
        for actor in plotter.renderer.actors:
            # Entferne orange/cyan Objekte (Motion rays + triangulated objects)
            if hasattr(actor, 'GetProperty'):
                prop = actor.GetProperty()
                if hasattr(prop, 'GetColor'):
                    color = prop.GetColor()
                    # Orange (1.0, 0.5, 0.0) und Cyan (0.0, 1.0, 1.0) Objekte entfernen
                    if (abs(color[0] - 1.0) < 0.1 and abs(color[1] - 0.5) < 0.1 and abs(color[2] - 0.0) < 0.1) or \
                       (abs(color[0] - 0.0) < 0.1 and abs(color[1] - 1.0) < 0.1 and abs(color[2] - 1.0) < 0.1):
                        actors_to_remove.append(actor)
        
        for actor in actors_to_remove:
            plotter.renderer.RemoveActor(actor)
    
    def _draw_live_camera_rays(self, plotter):
        """Zeichne Live-Sichtstrahlen von den Kameras"""
        current_time = time.time()
        ray_lifetime = 2.0  # 2 Sekunden sichtbar
        
        for camera_name, motion_list in self.camera_motion_data.items():
            if camera_name in self.camera_positions and motion_list:
                # Aktuelle Motion-Events
                recent_motions = [
                    motion for motion in motion_list
                    if current_time - motion['timestamp'] < ray_lifetime
                ]
                
                if recent_motions:
                    camera_pos = self.camera_positions[camera_name]
                    camera_color = self.camera_colors.get(camera_name, 'white')
                    
                    for motion in recent_motions[-3:]:  # Zeige letzte 3 Motions
                        # Berechne 3D Richtung
                        direction = self._pixel_to_3d_direction(motion['x'], motion['y'], camera_name)
                        
                        # Sichtstrahl mit Länge basierend auf Alter
                        age = current_time - motion['timestamp']
                        alpha = max(0.1, min(1.0, 1.0 - (age / ray_lifetime)))  # Sichere Opacity 0.1-1.0
                        ray_length = 5.0  # 5 Meter Strahl
                        
                        ray_end = camera_pos + direction * ray_length
                        
                        # Erstelle Strahl-Linie mit Float-Koordinaten
                        camera_pos_f = camera_pos.astype(np.float32)
                        ray_end_f = ray_end.astype(np.float32)
                        ray_line = pv.Line(camera_pos_f, ray_end_f)
                        plotter.add_mesh(ray_line, color='orange', line_width=3, 
                                       opacity=alpha, label=f'ray_{camera_name}')
                        
                        # Motion point am Ende des Strahls
                        motion_point = pv.Sphere(radius=0.08, center=ray_end_f)
                        plotter.add_mesh(motion_point, color=camera_color, opacity=alpha)
    
    def _calculate_live_triangulation(self, plotter):
        """Live-Berechnung der Triangulation mit kontinuierlichen Updates"""
        if len(self.camera_motion_data) < 2:
            return
            
        current_time = time.time()
        sync_window = 1.0  # 1 Sekunde Synchronisation
        
        # Sammle neueste synchrone Motion-Events
        synchronized_motions = {}
        
        for camera_name, motion_list in self.camera_motion_data.items():
            if camera_name in self.camera_positions and motion_list:
                # Neueste Events in Zeitfenster
                recent_motions = [
                    motion for motion in motion_list
                    if current_time - motion['timestamp'] < sync_window
                ]
                if recent_motions:
                    synchronized_motions[camera_name] = recent_motions[-1]
        
        if len(synchronized_motions) < 2:
            return
            
        # Berechne Triangulation für alle Kamera-Paare
        triangulated_points = []
        confidence_scores = []
        
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
                intersection, confidence = self._line_intersection_3d_with_confidence(pos1, dir1, pos2, dir2)
                if intersection is not None and confidence > 0.1:  # Mindest-Confidence
                    triangulated_points.append(intersection)
                    confidence_scores.append(confidence)
                    
                    # Zeige Triangulations-Punkt mit Confidence-basierter Größe
                    point_size = 0.05 + confidence * 0.15
                    intersection_f = intersection.astype(np.float32)
                    point_mesh = pv.Sphere(radius=point_size, center=intersection_f)
                    point_color = [1.0, 0.5, 0.0]  # Orange
                    plotter.add_mesh(point_mesh, color=point_color, opacity=0.8)
        
        # Finale Objekt-Position mit gewichteter Mittelung
        if triangulated_points:
            # Gewichtete Mittelung basierend auf Confidence
            total_weight = sum(confidence_scores)
            if total_weight > 0:
                weighted_position = np.zeros(3)
                for point, confidence in zip(triangulated_points, confidence_scores):
                    weighted_position += point * (confidence / total_weight)
                
                # Finale Live-Objekt-Position
                object_size = 0.15 + min(len(triangulated_points) * 0.05, 0.25)  # Größer bei mehr Übereinstimmungen
                final_object = pv.Sphere(radius=object_size, center=weighted_position)
                plotter.add_mesh(final_object, color='cyan', opacity=1.0)
                
                # Live-Koordinaten mit Confidence
                avg_confidence = np.mean(confidence_scores)
                coord_text = (f"🎯 LIVE OBJEKT\n"
                            f"X: {weighted_position[0]:.2f}m\n"
                            f"Y: {weighted_position[1]:.2f}m\n"
                            f"Z: {weighted_position[2]:.2f}m\n"
                            f"Confidence: {avg_confidence:.2f}")
                
                plotter.add_point_labels([weighted_position], [coord_text], 
                                       point_color='cyan', point_size=20, 
                                       font_size=10, text_color='white')
                
                # Live-Statistiken
                stats_text = (f"📊 LIVE TRIANGULATION\n"
                            f"Kamera-Paare: {len(triangulated_points)}\n"
                            f"Aktive Kameras: {len(synchronized_motions)}\n"
                            f"Sync-Fenster: {sync_window:.1f}s")
                plotter.add_text(stats_text, position='lower_right', font_size=9, color='cyan')
    
    def _line_intersection_3d_with_confidence(self, p1, d1, p2, d2):
        """Finde Kreuzungspunkt mit Confidence-Score"""
        w = p1 - p2
        a = np.dot(d1, d1)
        b = np.dot(d1, d2)
        c = np.dot(d2, d2)
        d = np.dot(d1, w)
        e = np.dot(d2, w)
        
        denominator = a * c - b * b
        if abs(denominator) < 1e-6:  # Parallel lines
            return None, 0.0
            
        t1 = (b * e - c * d) / denominator
        t2 = (a * e - b * d) / denominator
        
        # Berechne nächste Punkte auf beiden Linien
        closest1 = p1 + t1 * d1
        closest2 = p2 + t2 * d2
        
        # Mittelpunkt als Triangulation
        intersection = (closest1 + closest2) / 2
        
        # Confidence basierend auf Abstand zwischen den nächsten Punkten
        distance = np.linalg.norm(closest1 - closest2)
        confidence = max(0.0, 1.0 - distance / 2.0)  # Confidence sinkt mit Abstand
        
        # Zusätzliche Confidence-Faktoren
        # Winkel zwischen Strahlen (90° optimal)
        cos_angle = abs(np.dot(d1, d2))
        angle_confidence = 1.0 - cos_angle  # Besser wenn Strahlen senkrecht
        
        # Entfernung zu Kameras (nicht zu weit weg)
        dist1 = np.linalg.norm(intersection - p1)
        dist2 = np.linalg.norm(intersection - p2)
        distance_confidence = 1.0 / (1.0 + (dist1 + dist2) / 10.0)  # Näher ist besser
        
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
        """Konvertiere 2D Pixel-Koordinaten zu 3D Richtungsvektor - realistische 30° Rotation"""
        # Vereinfachte Kamera-Transformation
        # In einer echten Implementierung würden hier Kamera-Intrinsics verwendet
        
        # Normalisiere Pixel-Koordinaten zu [-1, 1]
        norm_x = (pixel_x - 320) / 320  # Annahme: 640x480 Auflösung
        norm_y = (pixel_y - 240) / 240
        
        # Standard Field of View Annahme (60° typisch für Webcams)
        fov_factor = 0.7  # Für 60° FOV
        
        # Basis-Richtung für jede Kamera (physisch nebeneinander, nur gedreht)
        if camera_name == 'webcam_0':
            # Links: 30° nach rechts gedreht (schauen sich zu)
            base_dir = np.array([0.5, 0.866, 0])  # 30° Rotation
            right_vec = np.array([0.866, -0.5, 0])  # Rechts-Vektor für diese Rotation
            up_vec = np.array([0, 0, 1])  # Z ist immer oben
        elif camera_name == 'webcam_1':
            # Rechts: 30° nach links gedreht (schauen sich zu)
            base_dir = np.array([-0.5, 0.866, 0])  # -30° Rotation
            right_vec = np.array([0.866, 0.5, 0])  # Rechts-Vektor für diese Rotation
            up_vec = np.array([0, 0, 1])  # Z ist immer oben
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
            
            # Close OpenCV windows
            try:
                cv2.destroyAllWindows()
                cv2.waitKey(1)
                time.sleep(0.1)  # Give windows time to close
                cv2.destroyAllWindows()  # Second attempt
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
                        # Test ob die Webcam wirklich verfügbar ist
                        ret, frame = cap.read()
                        if ret and frame is not None:
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
        
        # Process contours
        motion_count = 0
        result_frame = frame.copy()
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if min_area <= area <= max_area:
                motion_count += 1
                
                # Draw bounding box
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(result_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(result_frame, f'M{motion_count}', 
                           (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                           
                # Motion point für 3D viewer
                center_x = x + w // 2
                center_y = y + h // 2
                timestamp = time.time()
                self.motion_data.append((center_x, center_y, area, timestamp))
                
                # Kamera-spezifische Daten für Triangulation
                if stream_name not in self.camera_motion_data:
                    self.camera_motion_data[stream_name] = deque(maxlen=100)
                self.camera_motion_data[stream_name].append({
                    'x': center_x,
                    'y': center_y, 
                    'area': area,
                    'timestamp': timestamp,
                    'camera': stream_name
                })
                           
        # Add stream info
        timestamp_str = datetime.now().strftime("%H:%M:%S")
        cv2.putText(result_frame, f'{stream_name} - {timestamp_str}', 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(result_frame, f'Motions: {motion_count}', 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                   
        return result_frame, motion_count
        
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
                
                # Resize to same height
                height = min(frame1.shape[0], frame2.shape[0], 400)
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
                
                # Resize all frames to same size for grid
                target_width = 320  # Smaller for multiple views
                target_height = 240
                
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
