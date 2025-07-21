#!/usr/bin/env python3

import numpy as np
import pyvista as pv
import os

def load_voxel_grid(filename):
    """Load voxel grid from binary file"""
    with open(filename, "rb") as f:
        # Read metadata (N, voxel_size)
        N = int.from_bytes(f.read(4), byteorder='little')
        voxel_size = np.frombuffer(f.read(8), dtype=np.float64)[0]
        
        # Read voxel data
        voxel_data = np.frombuffer(f.read(), dtype=np.float32)
        voxel_grid = voxel_data.reshape((N, N, N))
    
    return voxel_grid, voxel_size

def visualize_webcam_voxels(voxel_file="voxel_webcam.bin"):
    """Visualize webcam-captured motion in 3D voxel space"""
    
    if not os.path.exists(voxel_file):
        print(f"Error: {voxel_file} not found!")
        print("Please run the webcam capture and voxel generation first.")
        return
    
    print(f"Loading voxel data from {voxel_file}...")
    voxel_grid, voxel_size = load_voxel_grid(voxel_file)
    
    print(f"Voxel grid shape: {voxel_grid.shape}")
    print(f"Voxel size: {voxel_size}")
    print(f"Value range: {voxel_grid.min()} to {voxel_grid.max()}")
    
    # Find non-zero voxels
    threshold = voxel_grid.max() * 0.1  # 10% of max value
    non_zero = voxel_grid > threshold
    
    if not np.any(non_zero):
        print("No significant voxel data found. Try capturing more motion.")
        return
    
    print(f"Voxels above threshold: {np.count_nonzero(non_zero)}")
    
    # Create 3D visualization
    plotter = pv.Plotter()
    plotter.set_background("black")
    
    # Get coordinates of non-zero voxels
    z, y, x = np.where(non_zero)
    values = voxel_grid[non_zero]
    
    # Create point cloud
    points = np.column_stack([x * voxel_size, y * voxel_size, z * voxel_size])
    
    # Create PyVista point cloud
    cloud = pv.PolyData(points)
    cloud["intensity"] = values
    
    # Add to plotter with color mapping
    plotter.add_mesh(cloud, 
                    scalars="intensity",
                    render_points_as_spheres=True,
                    point_size=5,
                    cmap="hot",
                    opacity=0.8)
    
    plotter.add_text("Webcam Motion Voxel Visualization", 
                    position='upper_left', font_size=12)
    
    plotter.show_axes()
    plotter.show_grid()
    
    print("\nInteractive 3D view opened. Close window to exit.")
    plotter.show()

if __name__ == "__main__":
    visualize_webcam_voxels()
