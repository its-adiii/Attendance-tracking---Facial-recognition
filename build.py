#!/usr/bin/env python3
"""
Render Build Script for AuraTrack
This script handles dependency installation properly
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    """Main build process"""
    print("🚀 Starting AuraTrack build process...")
    
    # Commands to run in order
    commands = [
        ("python -m pip install --upgrade pip setuptools wheel", "Updating pip"),
        ("pip install Flask==2.3.3 Flask-CORS==4.0.0", "Installing Flask"),
        ("pip install numpy==1.23.5", "Installing numpy"),
        ("pip install --no-cache-dir --force-reinstall Pillow==9.4.0", "Installing Pillow"),
        ("pip install opencv-python-headless==4.7.0.72", "Installing OpenCV"),
        ("pip install psycopg2-binary==2.9.6", "Installing PostgreSQL connector"),
        ("pip install configparser==5.3.0", "Installing config parser"),
    ]
    
    # Run each command
    for command, description in commands:
        if not run_command(command, description):
            print(f"❌ Build failed at: {description}")
            sys.exit(1)
    
    print("✅ All dependencies installed successfully!")
    print("🚀 Ready to start AuraTrack application...")
    
    # Start the application
    try:
        os.system("python clean_backend.py")
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
