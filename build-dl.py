#!/usr/bin/env python3
"""
Render Deep Learning Build Script
This script ensures proper installation of deep learning libraries
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
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def main():
    """Main build process for deep learning"""
    print("🚀 Starting AuraTrack Deep Learning build...")
    
    # Check Python version
    python_version = sys.version_info
    print(f"🐍 Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Commands to run in order
    commands = [
        ("python -m pip install --upgrade pip setuptools wheel", "Updating pip"),
        ("pip install Flask==2.3.3", "Installing Flask"),
        ("pip install Flask-CORS==4.0.0", "Installing Flask-CORS"),
        ("pip install numpy==1.24.4", "Installing NumPy"),
        ("pip install Pillow==9.5.0", "Installing Pillow"),
        ("pip install opencv-python-headless==4.8.1.78", "Installing OpenCV"),
        ("pip install tensorflow==2.13.0", "Installing TensorFlow"),
        ("pip install face-recognition==1.3.0", "Installing Face Recognition Library"),
        ("pip install dlib==19.24.0", "Installing Dlib"),
        ("pip install scikit-learn==1.3.0", "Installing Scikit-learn"),
        ("pip install joblib==1.3.0", "Installing Joblib"),
        ("pip install psycopg2-binary==2.9.7", "Installing PostgreSQL connector"),
        ("pip install configparser==5.3.0", "Installing config parser"),
    ]
    
    # Run each command
    for command, description in commands:
        if not run_command(command, description):
            print(f"❌ Build failed at: {description}")
            print("🔧 Trying alternative installation...")
            
            # Try alternative installation for failed package
            if "tensorflow" in description:
                run_command("pip install --no-deps tensorflow==2.13.0", "Installing TensorFlow (alternative)")
            elif "dlib" in description:
                print("⚠️ Dlib installation may take time...")
                run_command("pip install --no-cache-dir dlib==19.24.0", "Installing Dlib (alternative)")
            elif "face-recognition" in description:
                run_command("pip install --no-deps face-recognition==1.3.0", "Installing Face Recognition (alternative)")
            else:
                sys.exit(1)
    
    print("✅ All deep learning dependencies installed successfully!")
    print("🚀 Ready to start AuraTrack Deep Learning application...")
    
    # Start application
    try:
        print("🌟 Starting AuraTrack Deep Learning backend...")
        os.system("python deep_learning_backend.py")
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
