#!/usr/bin/env python3

import json
import numpy as np
from PIL import Image
import os

def create_test_data():
    # Create test images directory
    os.makedirs("motionimages", exist_ok=True)
    
    # Create some simple test images with motion
    frames = []
    for i in range(5):
        # Create a simple 100x100 image with a moving white dot
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # Moving dot position
        x = 20 + i * 15
        y = 50
        
        # Draw a larger white square (simulating a moving object)
        img[y-10:y+10, x-10:x+10] = [255, 255, 255]
        
        # Add some noise to make it more realistic
        noise = np.random.randint(0, 50, (100, 100, 3))
        img = np.clip(img.astype(int) + noise, 0, 255).astype(np.uint8)
        
        # Save image
        image_path = f"motionimages/frame_{i:03d}.png"
        Image.fromarray(img).save(image_path)
        print(f"Created {image_path} with moving object at x={x}")
        
        # Create frame metadata
        frame_info = {
            "filename": f"frame_{i:03d}.png",
            "timestamp": i * 0.1,  # 0.1 second intervals
            "camera_index": 0,
            "camera_x": 0.0,
            "camera_y": 0.0,
            "camera_z": 5.0,
            "rotation_x": 0.0,
            "rotation_y": 0.0,
            "rotation_z": 0.0
        }
        frames.append(frame_info)
    
    # The C++ code expects a JSON array, not an object
    with open("motionimages/metadata.json", "w") as f:
        json.dump(frames, f, indent=2)
    
    print("Test data created successfully!")
    print("- 5 test images in motionimages/")
    print("- metadata.json with frame information")

if __name__ == "__main__":
    create_test_data()
