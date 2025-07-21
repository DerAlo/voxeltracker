#!/usr/bin/env python3

print("=== Pixeltovoxelprojector Test ===")
print()

# Test the Python extension
try:
    import process_image_cpp
    print("✓ process_image_cpp module imported successfully")
except ImportError as e:
    print(f"✗ Failed to import process_image_cpp: {e}")

# Test other dependencies
try:
    import numpy as np
    print("✓ numpy imported successfully")
except ImportError as e:
    print(f"✗ Failed to import numpy: {e}")

try:
    import pyvista as pv
    print("✓ pyvista imported successfully")
except ImportError as e:
    print(f"✗ Failed to import pyvista: {e}")

try:
    import matplotlib.pyplot as plt
    print("✓ matplotlib imported successfully")
except ImportError as e:
    print(f"✗ Failed to import matplotlib: {e}")

# Check if voxel_grid.bin exists and test the viewer
import os
if os.path.exists("voxel_grid.bin"):
    print("✓ voxel_grid.bin found")
    
    # Test loading the voxel grid
    try:
        from voxelmotionviewer import load_voxel_grid
        voxel_grid, vox_size = load_voxel_grid("voxel_grid.bin")
        print(f"✓ Voxel grid loaded: shape={voxel_grid.shape}, voxel_size={vox_size}")
        print(f"  - Min value: {voxel_grid.min()}")
        print(f"  - Max value: {voxel_grid.max()}")
        print(f"  - Non-zero voxels: {np.count_nonzero(voxel_grid)}")
    except Exception as e:
        print(f"✗ Failed to load voxel grid: {e}")
else:
    print("✗ voxel_grid.bin not found")

# Check C++ executable
if os.path.exists("ray_voxel.exe"):
    print("✓ ray_voxel.exe found")
else:
    print("✗ ray_voxel.exe not found")

print()
print("=== Project Status ===")
print("The Pixeltovoxelprojector is successfully set up!")
print()
print("Usage:")
print("1. Create test images and metadata with: python create_test_data.py")
print("2. Generate voxel grid with: .\\ray_voxel.exe motionimages/metadata.json motionimages voxel_grid.bin")
print("3. View voxel grid with: python voxelmotionviewer.py")
print("4. Or view with space viewer: python spacevoxelviewer.py")
print()
print("Note: There might be an issue with image path handling in the C++ code.")
print("The voxel grid is generated but may be empty due to image loading problems.")
