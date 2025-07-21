#!/usr/bin/env python3

import os
import sys

print("Multi-Webcam Motion Tracker - Launcher")
print("=" * 40)
print(f"Current directory: {os.getcwd()}")
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")

# Check if main script exists
script_path = "webcam_motion_tracker.py"
if os.path.exists(script_path):
    print(f"✓ Found {script_path}")
    
    try:
        print("Starting Multi-Webcam Motion Tracker...")
        exec(open(script_path).read())
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"✗ {script_path} not found!")
    print("Available Python files:")
    for file in os.listdir("."):
        if file.endswith(".py"):
            print(f"  - {file}")
