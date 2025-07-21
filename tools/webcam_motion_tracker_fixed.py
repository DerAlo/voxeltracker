#!/usr/bin/env python3

import cv2
import numpy as np
import threading
import time
import queue
import tkinter as tk
from tkinter import ttk, messagebox
import pyvista as pv


class WebcamTracker:
    """Individual webcam motion tracker"""
    
    def __init__(self, camera_id, threshold=25, min_area=500):
        self.camera_id = camera_id
        self.threshold = threshold
        self.min_area = min_area
        self.cap = None
        self.prev_frame = None
        self.is_running = False
        self.thread = None
        self.motion_queue = queue.Queue(maxsize=50)
        
    def start(self):
        """Start camera capture"""
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            if not self.cap.isOpened():
                return False
                
            # Set lower resolution for better performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
            self.cap.set(cv2.CAP_PROP_FPS, 15)
            
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
        
        # Don't try to join the thread from within itself
        # Just mark as stopped and let it finish naturally
        
        # Release camera
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
                
        # Close window with proper cleanup
        try:
            cv2.destroyWindow(f'Camera {self.camera_id}')
            cv2.waitKey(1)  # Force window update
        except Exception:
            pass
            
    def _capture_loop(self):
        """Main capture and motion detection loop"""
        window_name = f'Camera {self.camera_id}'
        
        while self.is_running:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    print(f"Camera {self.camera_id}: Failed to read frame")
                    break
                    
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.GaussianBlur(gray, (5, 5), 0)
                
                if self.prev_frame is not None:
                    # Motion detection
                    frame_diff = cv2.absdiff(self.prev_frame, gray)
                    thresh = cv2.threshold(frame_diff, self.threshold, 255, cv2.THRESH_BINARY)[1]
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
                
        # Clean exit - don't call self.stop() here to avoid recursion
        print(f"Camera {self.camera_id} thread ending")


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
        with self.lock:
            current_time = time.time()
            
            for obj in motion_objects:
                # Convert 2D position to 3D voxel coordinates
                # Map camera view to voxel space
                x_norm = obj['x'] / obj['frame_width']  # 0-1
                y_norm = obj['y'] / obj['frame_height']  # 0-1
                z_norm = 0.5  # Middle depth for single camera
                
                # Multi-camera depth estimation (basic)
                if len(motion_objects) > 1:
                    cam_id = obj['camera_id']
                    z_norm = (cam_id * 0.3 + 0.2) % 1.0  # Distribute cameras in depth
                
                # Convert to voxel indices
                vx = int(x_norm * (self.size - 1))
                vy = int(y_norm * (self.size - 1))
                vz = int(z_norm * (self.size - 1))
                
                # Ensure indices are valid
                vx = max(0, min(vx, self.size - 1))
                vy = max(0, min(vy, self.size - 1))
                vz = max(0, min(vz, self.size - 1))
                
                # Add intensity based on motion area
                intensity = min(1.0, obj['area'] / 10000.0)
                self.grid[vz, vy, vx] += intensity
                
                # Add some spread for better visualization
                for dz in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            nz, ny, nx = vz + dz, vy + dy, vx + dx
                            if 0 <= nz < self.size and 0 <= ny < self.size and 0 <= nx < self.size:
                                self.grid[nz, ny, nx] += intensity * 0.3
            
            # Decay over time
            decay_factor = 0.95
            self.grid *= decay_factor
            
            # Threshold to prevent overflow
            self.grid = np.clip(self.grid, 0, 5.0)
    
    def get_visualization_data(self):
        """Get data for 3D visualization"""
        with self.lock:
            # Find active voxels
            threshold = 0.1
            indices = np.where(self.grid > threshold)
            
            if len(indices[0]) == 0:
                return np.array([]).reshape(0, 3), np.array([])
            
            # Convert indices to world coordinates
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
        
        # Handle window closing properly
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
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
        view_btn.grid(row=0, column=2, padx=5)
        
        # Settings section
        settings_frame = ttk.LabelFrame(main_frame, text="Motion Detection Settings", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Threshold setting
        ttk.Label(settings_frame, text="Threshold:").grid(row=0, column=0, sticky=tk.W)
        self.threshold_var = tk.IntVar(value=25)
        threshold_scale = ttk.Scale(settings_frame, from_=10, to=100, 
                                   variable=self.threshold_var, orient=tk.HORIZONTAL)
        threshold_scale.grid(row=0, column=1, sticky=tk.EW, padx=5)
        ttk.Label(settings_frame, textvariable=self.threshold_var).grid(row=0, column=2)
        
        # Min area setting
        ttk.Label(settings_frame, text="Min Area:").grid(row=1, column=0, sticky=tk.W)
        self.area_var = tk.IntVar(value=500)
        area_scale = ttk.Scale(settings_frame, from_=100, to=2000, 
                              variable=self.area_var, orient=tk.HORIZONTAL)
        area_scale.grid(row=1, column=1, sticky=tk.EW, padx=5)
        ttk.Label(settings_frame, textvariable=self.area_var).grid(row=1, column=2)
        
        settings_frame.columnconfigure(1, weight=1)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready - Click 'Detect Cameras' to start")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, 
                               relief=tk.SUNKEN, anchor=tk.W)
        status_label.pack(fill=tk.X, pady=(10, 0))
        
    def detect_cameras(self):
        """Detect available cameras"""
        self.camera_info.config(state=tk.NORMAL)
        self.camera_info.delete(1.0, tk.END)
        self.camera_info.insert(tk.END, "Detecting cameras...")
        self.camera_info.update()
        
        self.available_cameras = []
        
        # Test cameras 0-2 (reduced from 0-4 to prevent errors)
        for i in range(3):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, _ = cap.read()
                    if ret:
                        self.available_cameras.append(i)
                        self.camera_info.insert(tk.END, f"\nCamera {i}: Working")
                    else:
                        self.camera_info.insert(tk.END, f"\nCamera {i}: No signal")
                    cap.release()
                else:
                    self.camera_info.insert(tk.END, f"\nCamera {i}: Not available")
            except Exception as e:
                self.camera_info.insert(tk.END, f"\nCamera {i}: Error - {str(e)[:30]}")
                
        # Clear previous selections
        for widget in self.selection_frame.winfo_children():
            widget.destroy()
        self.camera_vars.clear()
        
        # Create checkboxes for available cameras
        if self.available_cameras:
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
                tracker = WebcamTracker(cam_id, threshold, min_area)
                if tracker.start():
                    self.cameras[cam_id] = tracker
                    success_count += 1
                    print(f"Started camera {cam_id}")
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
        if hasattr(self, 'cameras') and self.cameras:
            for tracker in self.cameras.values():
                tracker.stop()
            
            # Give threads time to clean up properly
            time.sleep(0.5)
            
            # Force close any remaining OpenCV windows
            try:
                cv2.destroyAllWindows()
                # Force window refresh
                cv2.waitKey(1)
            except Exception:
                pass
                
        self.cameras.clear()
        
        # Update GUI state only if widgets still exist
        try:
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.status_var.set("Tracking stopped")
        except Exception:
            # Widgets may have been destroyed during shutdown
            pass
        
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
        """Show 3D visualization window"""
        try:
            points, intensities = self.voxel_grid.get_visualization_data()
            
            if len(points) == 0:
                messagebox.showinfo("Info", "No motion data to visualize yet. Start tracking first!")
                return
                
            # Create PyVista plotter
            plotter = pv.Plotter(title="3D Motion Visualization")
            
            # Create point cloud
            point_cloud = pv.PolyData(points)
            point_cloud["intensity"] = intensities
            
            # Add to plotter with color mapping
            plotter.add_mesh(point_cloud, 
                           scalars="intensity",
                           cmap="hot",
                           point_size=8,
                           render_points_as_spheres=True)
            
            # Set camera and show
            plotter.camera_position = 'isometric'
            plotter.show_grid()
            plotter.add_axes()
            
            # Show in separate window (non-blocking)
            plotter.show(interactive=True)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show 3D view: {e}")
            
    def run(self):
        """Run the GUI"""
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"GUI error: {e}")
        finally:
            self.stop_tracking()
            
    def on_closing(self):
        """Handle window closing"""
        if self.is_tracking:
            self.stop_tracking()
        self.root.destroy()


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
