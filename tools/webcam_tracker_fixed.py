#!/usr/bin/env python3
"""
Multi-Webcam Motion Tracker & 3D Visualizer - FIXED VERSION
Real-time tracking using OpenCV and PyVista
"""

import cv2
import numpy as np
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
import pyvista as pv
import queue
import os


class WebcamTracker:
    """Single webcam motion tracking"""
    
    def __init__(self, camera_id, name="Camera"):
        self.camera_id = camera_id
        self.name = name
        self.cap = None
        self.is_running = False
        self.motion_data = []
        self.motion_queue = queue.Queue(maxsize=100)
        self.prev_frame = None
        self.lock = threading.Lock()
        
        # Detection parameters
        self.motion_threshold = 30
        self.min_area = 500
        
    def start(self):
        """Start camera capture"""
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            if not self.cap.isOpened():
                return False
                
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)  # Smaller for performance
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
            self.cap.set(cv2.CAP_PROP_FPS, 15)  # Lower FPS for stability
            
            # Test if we can actually read frames
            ret, test_frame = self.cap.read()
            if not ret:
                self.cap.release()
                return False
                
            self.is_running = True
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
            return True
            
        except Exception as e:
            print(f"Error starting camera {self.camera_id}: {e}")
            return False
            
    def stop(self):
        """Stop camera capture"""
        self.is_running = False
        if self.cap:
            self.cap.release()
        cv2.destroyWindow(f'Camera {self.camera_id}')
            
    def _capture_loop(self):
        """Main capture and motion detection loop"""
        window_name = f'Camera {self.camera_id}'
        
        while self.is_running:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    continue
                    
                # Motion detection
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.GaussianBlur(gray, (21, 21), 0)
                
                if self.prev_frame is not None:
                    # Frame difference
                    diff = cv2.absdiff(self.prev_frame, gray)
                    thresh = cv2.threshold(diff, self.motion_threshold, 255, cv2.THRESH_BINARY)[1]
                    thresh = cv2.dilate(thresh, None, iterations=2)
                    
                    # Find contours
                    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    
                    # Process detected motion
                    current_objects = []
                    for contour in contours:
                        area = cv2.contourArea(contour)
                        if area > self.min_area:
                            x, y, w, h = cv2.boundingRect(contour)
                            center_x = x + w // 2
                            center_y = y + h // 2
                            
                            # Store motion data
                            motion_obj = {
                                'camera_id': self.camera_id,
                                'timestamp': time.time(),
                                'x': center_x,
                                'y': center_y,
                                'area': area,
                                'frame_width': frame.shape[1],
                                'frame_height': frame.shape[0]
                            }
                            current_objects.append(motion_obj)
                            
                            # Draw detection
                            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                            cv2.circle(frame, (center_x, center_y), 3, (255, 0, 0), -1)
                    
                    # Add to motion queue (thread-safe)
                    if current_objects:
                        try:
                            self.motion_queue.put(current_objects, block=False)
                        except queue.Full:
                            pass
                        
                self.prev_frame = gray.copy()
                
                # Show frame with small size
                display_frame = cv2.resize(frame, (320, 240))
                cv2.putText(display_frame, f'Cam {self.camera_id}', (10, 20), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.imshow(window_name, display_frame)
                
                # Non-blocking key check
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:  # q or ESC
                    break
                    
                time.sleep(0.067)  # ~15 FPS
                
            except Exception as e:
                print(f"Camera {self.camera_id} error: {e}")
                break
                
        self.stop()


class VoxelGrid:
    """3D Voxel grid for motion visualization"""
    
    def __init__(self, size=50, scale=8.0):  # Smaller for performance
        self.size = size
        self.scale = scale
        self.grid = np.zeros((size, size, size), dtype=np.float32)
        self.start_time = time.time()
        self.lock = threading.Lock()
        
    def clear(self):
        """Clear the voxel grid"""
        with self.lock:
            self.grid.fill(0.0)
            self.start_time = time.time()
        
    def add_motion_data(self, motion_objects):
        """Add motion data to voxel grid"""
        if not motion_objects:
            return
            
        with self.lock:
            for motion in motion_objects:
                # Convert pixel to normalized coordinates
                px = motion['x'] / motion['frame_width']   # 0 to 1
                py = motion['y'] / motion['frame_height']  # 0 to 1
                
                # Simple 3D projection
                world_x = (px - 0.5) * self.scale
                world_y = (0.5 - py) * self.scale * 0.75  # Flip Y and aspect ratio
                
                # Use time for Z dimension
                elapsed = motion['timestamp'] - self.start_time
                world_z = elapsed * 1.0  # 1 unit per second
                
                # Convert to voxel indices
                vx = int((world_x + self.scale/2) / self.scale * self.size)
                vy = int((world_y + self.scale*0.375) / (self.scale*0.75) * self.size)
                vz = int(world_z / 5.0 * self.size)  # 5 seconds depth
                
                # Clamp to bounds
                vx = max(0, min(self.size - 1, vx))
                vy = max(0, min(self.size - 1, vy))
                vz = max(0, min(self.size - 1, vz))
                
                # Add motion intensity
                intensity = min(1.0, motion['area'] / 3000.0)
                self.grid[vz, vy, vx] += intensity
            
    def get_point_cloud(self, threshold=0.1):
        """Extract point cloud from voxel grid"""
        with self.lock:
            indices = np.nonzero(self.grid > threshold)
            
            if len(indices[0]) == 0:
                return None, None
                
            # Convert to world coordinates
            points = np.column_stack([
                (indices[2] / self.size) * self.scale - self.scale/2,  # X
                (indices[1] / self.size) * self.scale*0.75 - self.scale*0.375,  # Y
                (indices[0] / self.size) * 5.0  # Z
            ])
            
            intensities = self.grid[indices]
            return points.copy(), intensities.copy()


class MultiWebcamGUI:
    """Main GUI for multi-webcam tracking"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Multi-Webcam Motion Tracker")
        self.root.geometry("500x600")
        
        # Prevent window from being resized to avoid widget conflicts
        self.root.resizable(False, False)
        
        self.cameras = {}
        self.voxel_grid = VoxelGrid()
        self.is_tracking = False
        self.update_thread = None
        self.available_cameras = []
        
        self.setup_gui()
        
    def setup_gui(self):
        """Setup the GUI with unique widget names"""
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_lbl = ttk.Label(main_frame, text="Multi-Webcam Motion Tracker", 
                             font=("Arial", 14, "bold"))
        title_lbl.pack(pady=(0, 10))
        
        # Camera detection section
        detect_frame = ttk.LabelFrame(main_frame, text="Camera Detection", padding="10")
        detect_frame.pack(fill=tk.X, pady=(0, 10))
        
        detect_btn = ttk.Button(detect_frame, text="Detect Cameras", 
                               command=self.detect_cameras)
        detect_btn.pack()
        
        self.camera_info = tk.Text(detect_frame, height=3, width=50, state=tk.DISABLED)
        self.camera_info.pack(pady=(10, 0))
        
        # Camera selection section
        select_frame = ttk.LabelFrame(main_frame, text="Camera Selection", padding="10")
        select_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.camera_vars = {}
        self.selection_frame = ttk.Frame(select_frame)
        self.selection_frame.pack()
        
        # Control section
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Control buttons
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack()
        
        self.start_btn = ttk.Button(btn_frame, text="Start Tracking", 
                                   command=self.start_tracking)
        self.start_btn.grid(row=0, column=0, padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="Stop Tracking", 
                                  command=self.stop_tracking, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        view_btn = ttk.Button(btn_frame, text="3D View", 
                             command=self.show_3d_view)
        view_btn.grid(row=1, column=0, padx=5, pady=5)
        
        clear_btn = ttk.Button(btn_frame, text="Clear Data", 
                              command=self.clear_voxels)
        clear_btn.grid(row=1, column=1, padx=5, pady=5)
        
        # Settings section
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Threshold setting
        threshold_frame = ttk.Frame(settings_frame)
        threshold_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(threshold_frame, text="Motion Threshold:").pack(side=tk.LEFT)
        self.threshold_var = tk.IntVar(value=30)
        threshold_scale = ttk.Scale(threshold_frame, from_=10, to=100, 
                                   variable=self.threshold_var, orient=tk.HORIZONTAL, length=200)
        threshold_scale.pack(side=tk.RIGHT)
        
        # Min area setting
        area_frame = ttk.Frame(settings_frame)
        area_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(area_frame, text="Min Area:").pack(side=tk.LEFT)
        self.area_var = tk.IntVar(value=500)
        area_scale = ttk.Scale(area_frame, from_=100, to=2000, 
                              variable=self.area_var, orient=tk.HORIZONTAL, length=200)
        area_scale.pack(side=tk.RIGHT)
        
        # Status
        self.status_var = tk.StringVar(value="Ready - Click 'Detect Cameras' to start")
        status_lbl = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W, padding="5")
        status_lbl.pack(fill=tk.X, pady=(10, 0))
        
    def detect_cameras(self):
        """Detect available cameras with better error handling"""
        self.camera_info.config(state=tk.NORMAL)
        self.camera_info.delete(1.0, tk.END)
        self.camera_info.insert(tk.END, "Detecting cameras...\n")
        self.root.update()
        
        # Clear previous selections
        for widget in self.selection_frame.winfo_children():
            widget.destroy()
        self.camera_vars.clear()
        
        # Test cameras with better error handling
        self.available_cameras = []
        for i in range(3):  # Test only 0-2 to avoid errors
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    # Try to read a frame to verify it works
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        self.available_cameras.append(i)
                        self.camera_info.insert(tk.END, f"✓ Camera {i}: Working\n")
                cap.release()
            except Exception as e:
                self.camera_info.insert(tk.END, f"✗ Camera {i}: Error - {e}\n")
                
        if not self.available_cameras:
            self.camera_info.insert(tk.END, "No working cameras found!")
            self.status_var.set("No cameras detected")
        else:
            # Create checkboxes for available cameras
            for i, cam_id in enumerate(self.available_cameras):
                var = tk.BooleanVar()
                self.camera_vars[cam_id] = var
                
                cb = ttk.Checkbutton(self.selection_frame, 
                                    text=f"Camera {cam_id}", 
                                    variable=var)
                cb.grid(row=i//2, column=i%2, sticky=tk.W, padx=10, pady=2)
                
            self.status_var.set(f"Found {len(self.available_cameras)} working cameras")
                
        self.camera_info.config(state=tk.DISABLED)
        
    def start_tracking(self):
        """Start motion tracking"""
        # Get selected cameras
        selected_cameras = [cam_id for cam_id, var in self.camera_vars.items() if var.get()]
        
        if not selected_cameras:
            messagebox.showwarning("Warning", "Please select at least one camera")
            return
            
        # Update settings
        threshold = self.threshold_var.get()
        min_area = self.area_var.get()
        
        # Start cameras
        self.cameras = {}
        success_count = 0
        
        for cam_id in selected_cameras:
            try:
                tracker = WebcamTracker(cam_id, f"Camera {cam_id}")
                tracker.motion_threshold = threshold
                tracker.min_area = min_area
                
                if tracker.start():
                    self.cameras[cam_id] = tracker
                    success_count += 1
                else:
                    print(f"Failed to start camera {cam_id}")
                    
            except Exception as e:
                print(f"Error with camera {cam_id}: {e}")
                
        if success_count > 0:
            self.is_tracking = True
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.voxel_grid.clear()
            
            # Start update thread
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
            
            self.status_var.set(f"Tracking with {success_count} cameras - Press 'q' in camera windows to close them")
        else:
            self.status_var.set("Failed to start any cameras")
            messagebox.showerror("Error", "Could not start any cameras")
            
    def stop_tracking(self):
        """Stop motion tracking"""
        self.is_tracking = False
        
        # Stop all cameras
        for tracker in self.cameras.values():
            tracker.stop()
        
        # Close all OpenCV windows
        cv2.destroyAllWindows()
        
        self.cameras.clear()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("Tracking stopped")
        
    def _update_loop(self):
        """Update loop for processing motion data"""
        while self.is_tracking:
            try:
                # Collect motion data from all cameras
                all_motion_data = []
                for tracker in self.cameras.values():
                    try:
                        while True:
                            motion_objects = tracker.motion_queue.get_nowait()
                            all_motion_data.extend(motion_objects)
                    except queue.Empty:
                        continue
                        
                # Add to voxel grid
                if all_motion_data:
                    self.voxel_grid.add_motion_data(all_motion_data)
                    
                time.sleep(0.1)  # Update every 100ms
                
            except Exception as e:
                print(f"Update loop error: {e}")
                break
            
    def show_3d_view(self):
        """Show 3D visualization"""
        try:
            points, intensities = self.voxel_grid.get_point_cloud(threshold=0.05)
            
            if points is None or len(points) == 0:
                messagebox.showinfo("Info", 
                    "No motion data to visualize.\n\n"
                    "1. Start tracking\n"
                    "2. Move objects in front of cameras\n"
                    "3. Wait a few seconds\n"
                    "4. Try again")
                return
                
            # Create PyVista plot
            plotter = pv.Plotter(title=f"3D Motion - {len(points)} points")
            plotter.set_background("black")
            
            # Create point cloud
            cloud = pv.PolyData(points)
            cloud["intensity"] = intensities
            
            # Add to plot
            plotter.add_mesh(cloud, 
                           scalars="intensity",
                           render_points_as_spheres=True,
                           point_size=8,
                           cmap="hot",
                           opacity=0.9)
            
            # Add coordinate system
            plotter.show_axes()
            
            # Show plot
            plotter.show()
            
        except Exception as e:
            messagebox.showerror("Error", f"3D visualization failed:\n{e}")
            
    def clear_voxels(self):
        """Clear voxel data"""
        self.voxel_grid.clear()
        self.status_var.set("Voxel data cleared")
        
    def run(self):
        """Run the application"""
        # Set up proper cleanup
        def on_closing():
            self.stop_tracking()
            self.root.destroy()
            
        self.root.protocol("WM_DELETE_WINDOW", on_closing)
        
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"GUI error: {e}")
        finally:
            self.stop_tracking()


def main():
    """Main entry point"""
    print("Multi-Webcam Motion Tracker & 3D Visualizer")
    print("=" * 50)
    print("Starting application...")
    
    try:
        app = MultiWebcamGUI()
        app.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Application error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
