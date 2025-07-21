#!/usr/bin/env python3
"""
Multi-Webcam Object Tracking & 3D Voxel Visualization
Real-time tracking of moving objects using multiple webcams with 3D voxel display
"""

import cv2
import numpy as np
import threading
import time
import json
from datetime import datetime
from pathlib import Path
import queue
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pyvista as pv
from pyvistaqt import QtInteractor
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget
import sys


class WebcamCapture:
    """Handles single webcam capture and motion detection"""
    
    def __init__(self, camera_id, camera_name):
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.cap = None
        self.is_running = False
        self.frame_queue = queue.Queue(maxsize=10)
        self.motion_queue = queue.Queue(maxsize=100)
        self.prev_frame = None
        self.frame_count = 0
        
        # Motion detection parameters
        self.motion_threshold = 25
        self.min_contour_area = 100
        
    def start(self):
        """Start webcam capture"""
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            raise Exception(f"Cannot open camera {self.camera_id}")
            
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        self.is_running = True
        self.capture_thread = threading.Thread(target=self._capture_loop)
        self.capture_thread.daemon = True
        self.capture_thread.start()
        
    def stop(self):
        """Stop webcam capture"""
        self.is_running = False
        if self.capture_thread:
            self.capture_thread.join()
        if self.cap:
            self.cap.release()
            
    def _capture_loop(self):
        """Main capture loop with motion detection"""
        while self.is_running:
            ret, frame = self.cap.read()
            if not ret:
                continue
                
            # Convert to grayscale for motion detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            
            # Motion detection
            if self.prev_frame is not None:
                frame_delta = cv2.absdiff(self.prev_frame, gray)
                thresh = cv2.threshold(frame_delta, self.motion_threshold, 255, cv2.THRESH_BINARY)[1]
                thresh = cv2.dilate(thresh, None, iterations=2)
                
                # Find contours
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # Process motion
                motion_objects = []
                for contour in contours:
                    if cv2.contourArea(contour) > self.min_contour_area:
                        x, y, w, h = cv2.boundingRect(contour)
                        center_x = x + w // 2
                        center_y = y + h // 2
                        
                        motion_objects.append({
                            'camera_id': self.camera_id,
                            'camera_name': self.camera_name,
                            'timestamp': time.time(),
                            'frame_count': self.frame_count,
                            'center_x': center_x,
                            'center_y': center_y,
                            'width': w,
                            'height': h,
                            'area': cv2.contourArea(contour)
                        })
                        
                        # Draw bounding box on frame
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        cv2.circle(frame, (center_x, center_y), 5, (255, 0, 0), -1)
                
                # Add motion data to queue
                if motion_objects:
                    try:
                        self.motion_queue.put(motion_objects, block=False)
                    except queue.Full:
                        pass
            
            self.prev_frame = gray.copy()
            self.frame_count += 1
            
            # Add frame to display queue
            try:
                self.frame_queue.put(frame, block=False)
            except queue.Full:
                # Remove old frame
                try:
                    self.frame_queue.get_nowait()
                    self.frame_queue.put(frame, block=False)
                except queue.Empty:
                    pass
                    
            time.sleep(0.033)  # ~30 FPS


class MultiCameraTracker:
    """Manages multiple webcam captures and coordinates tracking"""
    
    def __init__(self):
        self.cameras = {}
        self.is_tracking = False
        self.motion_data = []
        self.start_time = None
        
    def add_camera(self, camera_id, camera_name):
        """Add a webcam to the tracking system"""
        if camera_id not in self.cameras:
            self.cameras[camera_id] = WebcamCapture(camera_id, camera_name)
            return True
        return False
        
    def remove_camera(self, camera_id):
        """Remove a webcam from tracking"""
        if camera_id in self.cameras:
            self.cameras[camera_id].stop()
            del self.cameras[camera_id]
            return True
        return False
        
    def start_tracking(self):
        """Start tracking with all cameras"""
        if not self.cameras:
            return False
            
        self.motion_data = []
        self.start_time = time.time()
        self.is_tracking = True
        
        # Start all cameras
        for camera in self.cameras.values():
            try:
                camera.start()
            except Exception as e:
                print(f"Failed to start camera {camera.camera_name}: {e}")
                return False
                
        # Start motion collection thread
        self.collection_thread = threading.Thread(target=self._collect_motion_data)
        self.collection_thread.daemon = True
        self.collection_thread.start()
        
        return True
        
    def stop_tracking(self):
        """Stop tracking"""
        self.is_tracking = False
        
        # Stop all cameras
        for camera in self.cameras.values():
            camera.stop()
            
    def _collect_motion_data(self):
        """Collect motion data from all cameras"""
        while self.is_tracking:
            for camera in self.cameras.values():
                try:
                    motion_objects = camera.motion_queue.get_nowait()
                    self.motion_data.extend(motion_objects)
                except queue.Empty:
                    continue
            time.sleep(0.01)
            
    def get_camera_frame(self, camera_id):
        """Get latest frame from specific camera"""
        if camera_id in self.cameras:
            try:
                return self.cameras[camera_id].frame_queue.get_nowait()
            except queue.Empty:
                return None
        return None


class VoxelProcessor:
    """Processes motion data into 3D voxel space"""
    
    def __init__(self, grid_size=100, voxel_size=0.1):
        self.grid_size = grid_size
        self.voxel_size = voxel_size
        self.voxel_grid = np.zeros((grid_size, grid_size, grid_size), dtype=np.float32)
        
    def reset_grid(self):
        """Reset voxel grid"""
        self.voxel_grid.fill(0.0)
        
    def process_motion_data(self, motion_data, camera_positions=None):
        """Convert motion data to voxel space"""
        if not motion_data:
            return
            
        # Default camera positions if not provided
        if camera_positions is None:
            camera_positions = {}
            
        # Process each motion event
        for motion in motion_data:
            camera_id = motion['camera_id']
            
            # Get camera position (default to simple layout)
            if camera_id in camera_positions:
                cam_pos = camera_positions[camera_id]
            else:
                # Default positioning - spread cameras around
                angle = (camera_id * 60) * np.pi / 180  # 60 degrees apart
                cam_pos = {
                    'x': 5 * np.cos(angle),
                    'y': 5 * np.sin(angle), 
                    'z': 2.0
                }
            
            # Convert pixel coordinates to 3D space
            # Simple perspective projection
            pixel_x = motion['center_x'] / 640.0  # Normalize to [0,1]
            pixel_y = motion['center_y'] / 480.0
            
            # Project to 3D world coordinates
            world_x = (pixel_x - 0.5) * 10  # Scale to world units
            world_y = (pixel_y - 0.5) * 7.5
            world_z = motion['timestamp'] * 0.1  # Use time as Z dimension
            
            # Convert to voxel indices
            voxel_x = int((world_x + 5) / 10 * self.grid_size)
            voxel_y = int((world_y + 3.75) / 7.5 * self.grid_size)  
            voxel_z = int(world_z / 10 * self.grid_size)
            
            # Clamp to grid bounds
            voxel_x = max(0, min(self.grid_size - 1, voxel_x))
            voxel_y = max(0, min(self.grid_size - 1, voxel_y))
            voxel_z = max(0, min(self.grid_size - 1, voxel_z))
            
            # Add motion intensity to voxel
            intensity = motion['area'] / 10000.0  # Normalize area
            self.voxel_grid[voxel_z, voxel_y, voxel_x] += intensity
            
    def get_voxel_points(self, threshold=0.1):
        """Extract point cloud from voxel grid"""
        indices = np.where(self.voxel_grid > threshold)
        if len(indices[0]) == 0:
            return None, None
            
        # Convert indices to world coordinates
        points = np.column_stack([
            indices[2] * self.voxel_size,  # X
            indices[1] * self.voxel_size,  # Y  
            indices[0] * self.voxel_size   # Z
        ])
        
        intensities = self.voxel_grid[indices]
        return points, intensities


class MotionTrackerGUI:
    """Main GUI for the multi-camera motion tracker"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Multi-Webcam Motion Tracker & 3D Visualizer")
        self.root.geometry("1200x800")
        
        self.tracker = MultiCameraTracker()
        self.voxel_processor = VoxelProcessor()
        
        self.is_tracking = False
        self.qt_app = None
        self.plotter_widget = None
        
        self.setup_gui()
        self.setup_display_update()
        
    def setup_gui(self):
        """Setup the GUI layout"""
        
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Camera controls
        left_frame = ttk.LabelFrame(main_frame, text="Camera Controls", width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)
        
        # Camera list
        ttk.Label(left_frame, text="Available Cameras:").pack(pady=(10, 5))
        
        camera_frame = ttk.Frame(left_frame)
        camera_frame.pack(fill=tk.X, padx=10)
        
        self.camera_listbox = tk.Listbox(camera_frame, height=6)
        self.camera_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(camera_frame, orient=tk.VERTICAL, command=self.camera_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.camera_listbox.config(yscrollcommand=scrollbar.set)
        
        # Camera buttons
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Detect Cameras", command=self.detect_cameras).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Add Camera", command=self.add_camera_dialog).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="Remove Camera", command=self.remove_camera).pack(fill=tk.X, pady=2)
        
        # Tracking controls
        ttk.Separator(left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(left_frame, text="Tracking Controls:").pack(pady=(10, 5))
        
        control_frame = ttk.Frame(left_frame)
        control_frame.pack(fill=tk.X, padx=10)
        
        self.start_btn = ttk.Button(control_frame, text="Start Tracking", command=self.start_tracking)
        self.start_btn.pack(fill=tk.X, pady=2)
        
        self.stop_btn = ttk.Button(control_frame, text="Stop Tracking", command=self.stop_tracking, state=tk.DISABLED)
        self.stop_btn.pack(fill=tk.X, pady=2)
        
        ttk.Button(control_frame, text="Clear Voxels", command=self.clear_voxels).pack(fill=tk.X, pady=2)
        
        # Status
        ttk.Separator(left_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=10)
        self.status_label = ttk.Label(left_frame, text="Status: Ready")
        self.status_label.pack(pady=10)
        
        # Right panel - Video display and 3D visualization
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Video displays (top)
        video_frame = ttk.LabelFrame(right_frame, text="Camera Feeds")
        video_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.video_canvas_frame = ttk.Frame(video_frame)
        self.video_canvas_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 3D Visualization (bottom)
        viz_frame = ttk.LabelFrame(right_frame, text="3D Motion Visualization")
        viz_frame.pack(fill=tk.BOTH, expand=True)
        
        self.setup_3d_viewer(viz_frame)
        
    def setup_3d_viewer(self, parent):
        """Setup the 3D visualization widget"""
        try:
            if self.qt_app is None:
                self.qt_app = QApplication.instance()
                if self.qt_app is None:
                    self.qt_app = QApplication([])
            
            # Create Qt widget for PyVista
            self.qt_widget = QWidget()
            layout = QVBoxLayout()
            
            self.plotter = pv.Plotter(notebook=False, off_screen=False)
            self.plotter.set_background("black")
            
            # Create QtInteractor
            self.plotter_widget = QtInteractor(parent, plotter=self.plotter)
            layout.addWidget(self.plotter_widget)
            self.qt_widget.setLayout(layout)
            
            # Embed Qt widget in Tkinter (this is tricky, using basic setup)
            viz_label = ttk.Label(parent, text="3D Visualization will update here")
            viz_label.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
            
        except Exception as e:
            print(f"3D viewer setup failed: {e}")
            viz_label = ttk.Label(parent, text="3D Visualization unavailable")
            viz_label.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
    
    def detect_cameras(self):
        """Detect available cameras"""
        self.camera_listbox.delete(0, tk.END)
        
        # Test camera indices 0-4
        available_cameras = []
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available_cameras.append(f"Camera {i}")
                cap.release()
        
        if available_cameras:
            for cam in available_cameras:
                self.camera_listbox.insert(tk.END, cam)
        else:
            self.camera_listbox.insert(tk.END, "No cameras detected")
            
        self.update_status(f"Detected {len(available_cameras)} cameras")
    
    def add_camera_dialog(self):
        """Dialog to add a camera"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Camera")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Camera ID:").pack(pady=5)
        id_var = tk.StringVar(value="0")
        ttk.Entry(dialog, textvariable=id_var).pack(pady=5)
        
        ttk.Label(dialog, text="Camera Name:").pack(pady=5)
        name_var = tk.StringVar(value="Camera 0")
        ttk.Entry(dialog, textvariable=name_var).pack(pady=5)
        
        def add_camera():
            try:
                camera_id = int(id_var.get())
                camera_name = name_var.get()
                
                if self.tracker.add_camera(camera_id, camera_name):
                    self.camera_listbox.insert(tk.END, f"{camera_name} (ID: {camera_id})")
                    self.update_status(f"Added {camera_name}")
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", "Camera already added")
            except ValueError:
                messagebox.showerror("Error", "Invalid camera ID")
        
        ttk.Button(dialog, text="Add", command=add_camera).pack(pady=10)
    
    def remove_camera(self):
        """Remove selected camera"""
        selection = self.camera_listbox.curselection()
        if selection:
            camera_text = self.camera_listbox.get(selection[0])
            # Extract camera ID from text
            try:
                camera_id = int(camera_text.split("ID: ")[1].split(")")[0])
                if self.tracker.remove_camera(camera_id):
                    self.camera_listbox.delete(selection[0])
                    self.update_status(f"Removed camera {camera_id}")
            except:
                messagebox.showerror("Error", "Cannot remove camera")
    
    def start_tracking(self):
        """Start the tracking process"""
        if not self.tracker.cameras:
            messagebox.showwarning("Warning", "No cameras added")
            return
            
        if self.tracker.start_tracking():
            self.is_tracking = True
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.update_status("Tracking started")
            self.voxel_processor.reset_grid()
        else:
            messagebox.showerror("Error", "Failed to start tracking")
    
    def stop_tracking(self):
        """Stop the tracking process"""
        self.tracker.stop_tracking()
        self.is_tracking = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.update_status("Tracking stopped")
    
    def clear_voxels(self):
        """Clear the voxel grid"""
        self.voxel_processor.reset_grid()
        self.update_status("Voxel grid cleared")
    
    def update_status(self, message):
        """Update status label"""
        self.status_label.config(text=f"Status: {message}")
    
    def setup_display_update(self):
        """Setup periodic display updates"""
        self.update_displays()
        self.root.after(100, self.setup_display_update)  # Update every 100ms
    
    def update_displays(self):
        """Update video displays and 3D visualization"""
        if self.is_tracking:
            # Process motion data
            if self.tracker.motion_data:
                self.voxel_processor.process_motion_data(self.tracker.motion_data)
                
                # Update 3D visualization
                self.update_3d_visualization()
                
                # Clear processed motion data
                self.tracker.motion_data = []
    
    def update_3d_visualization(self):
        """Update the 3D voxel visualization"""
        try:
            points, intensities = self.voxel_processor.get_voxel_points(threshold=0.05)
            
            if points is not None and self.plotter is not None:
                self.plotter.clear()
                
                # Create point cloud
                cloud = pv.PolyData(points)
                cloud["intensity"] = intensities
                
                # Add to plotter
                self.plotter.add_mesh(cloud, 
                                    scalars="intensity",
                                    render_points_as_spheres=True,
                                    point_size=8,
                                    cmap="hot",
                                    opacity=0.8)
                
                self.plotter.render()
                
        except Exception as e:
            print(f"3D visualization update failed: {e}")
    
    def run(self):
        """Run the GUI"""
        self.detect_cameras()  # Auto-detect cameras on startup
        self.root.mainloop()


def main():
    """Main entry point"""
    print("Multi-Webcam Motion Tracker & 3D Visualizer")
    print("=" * 50)
    
    # Create and run GUI
    app = MotionTrackerGUI()
    app.run()


if __name__ == "__main__":
    main()
