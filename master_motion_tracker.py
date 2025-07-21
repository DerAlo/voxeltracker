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
    "📷 Local Webcam": {
        "type": "webcam",
        "source": 0,
        "description": "Standard USB-Webcam"
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
        
        # Advanced settings (collapsible)
        self.settings_visible = False
        self.settings_btn = ttk.Button(control_frame, text="⚙️ Advanced Settings", 
                                      command=self.toggle_settings)
        self.settings_btn.pack(side=tk.LEFT, padx=5)
        
        # Advanced settings frame (initially hidden)
        self.settings_frame = ttk.LabelFrame(self.root, text="🔧 Advanced Settings")
        
        # Threshold
        ttk.Label(self.settings_frame, text="Motion Threshold:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.threshold_var = tk.IntVar(value=25)
        threshold_scale = ttk.Scale(self.settings_frame, from_=5, to=100, 
                                   variable=self.threshold_var, orient=tk.HORIZONTAL)
        threshold_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Label(self.settings_frame, textvariable=self.threshold_var).grid(row=0, column=2, padx=5)
        
        # Min area
        ttk.Label(self.settings_frame, text="Min Object Size:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.min_area_var = tk.IntVar(value=100)
        min_area_scale = ttk.Scale(self.settings_frame, from_=1, to=1000, 
                                  variable=self.min_area_var, orient=tk.HORIZONTAL)
        min_area_scale.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Label(self.settings_frame, textvariable=self.min_area_var).grid(row=1, column=2, padx=5)
        
        # Max area
        ttk.Label(self.settings_frame, text="Max Object Size:").grid(row=2, column=0, sticky=tk.W, padx=5)
        self.max_area_var = tk.IntVar(value=10000)
        max_area_scale = ttk.Scale(self.settings_frame, from_=100, to=50000, 
                                  variable=self.max_area_var, orient=tk.HORIZONTAL)
        max_area_scale.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Label(self.settings_frame, textvariable=self.max_area_var).grid(row=2, column=2, padx=5)
        
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
        else:
            self.url_frame.grid_remove()
            
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
                    # Create point cloud
                    point_cloud = pv.PolyData(points)
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
        else:
            self.settings_frame.pack(pady=5, padx=10, fill=tk.X, before=self.root.children['!labelframe3'])
            self.settings_btn.config(text="🔼 Hide Settings")
            self.settings_visible = True
            
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
        self.is_tracking = False
        
        # Wait a moment for tracking loop to notice
        time.sleep(0.1)
        
        # Close OpenCV windows first
        try:
            cv2.destroyAllWindows()
        except Exception as e:
            self.log(f"⚠️ OpenCV Window-Cleanup Warnung: {str(e)}")
            
        # Release captures safely
        for name, cap in list(self.caps.items()):
            try:
                if cap and hasattr(cap, 'isOpened') and cap.isOpened():
                    cap.release()
                    self.log(f"✅ {name} capture released")
            except Exception as e:
                self.log(f"⚠️ {name} release Warnung: {str(e)}")
                
        self.caps.clear()
        self.bg_subtractors.clear()
        
        # Update GUI safely
        try:
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.status_var.set("⏹️ Motion Tracking gestoppt")
            self.log("✅ Motion Tracking erfolgreich gestoppt")
        except Exception as e:
            self.log(f"⚠️ GUI Update Warnung: {str(e)}")
            
        # Force garbage collection
        import gc
        gc.collect()
        
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
                self.caps['webcam'] = cap
                self.bg_subtractors['webcam'] = cv2.createBackgroundSubtractorMOG2()
                self.log("✅ Webcam initialisiert")
                return True
            else:
                self.log("❌ Webcam konnte nicht geöffnet werden")
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
                           
                # Store motion data for 3D visualization
                center_x = x + w // 2
                center_y = y + h // 2
                timestamp = time.time()
                self.motion_data.append((center_x, center_y, area, timestamp))
                           
        # Add stream info
        timestamp_str = datetime.now().strftime("%H:%M:%S")
        cv2.putText(result_frame, f'{stream_name} - {timestamp_str}', 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(result_frame, f'Motions: {motion_count}', 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                   
        return result_frame, motion_count
        
    def _display_frames(self, frames, motion_counts, frame_count, start_time):
        """Display processed frames"""
        try:
            if len(frames) == 1:
                # Single frame display
                name, frame = list(frames.items())[0]
                fps = frame_count / (time.time() - start_time + 0.001)
                cv2.putText(frame, f'FPS: {fps:.1f}', 
                           (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                cv2.imshow(f'Motion Tracker - {name}', frame)
                
            elif len(frames) >= 2:
                # Side-by-side dual display
                stream_names = list(frames.keys())
                frame1 = frames[stream_names[0]]
                frame2 = frames[stream_names[1]]
                
                # Resize to same height
                height = min(frame1.shape[0], frame2.shape[0], 400)
                frame1_resized = cv2.resize(frame1, (int(frame1.shape[1] * height / frame1.shape[0]), height))
                frame2_resized = cv2.resize(frame2, (int(frame2.shape[1] * height / frame2.shape[0]), height))
                
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
