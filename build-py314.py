#!/usr/bin/env python3
"""
Render Python 3.14 Build Script
This script works with Python 3.14
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
    """Main build process for Python 3.14"""
    print("🚀 Starting AuraTrack build for Python 3.14...")
    
    # Check Python version
    python_version = sys.version_info
    print(f"🐍 Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Commands to run in order
    commands = [
        ("python -m pip install --upgrade pip setuptools wheel", "Updating pip"),
        ("pip install Flask==2.3.3", "Installing Flask"),
        ("pip install Flask-CORS==4.0.0", "Installing Flask-CORS"),
        ("pip install numpy==1.26.4", "Installing numpy"),
        ("pip install Pillow==10.2.0", "Installing Pillow"),
        ("pip install opencv-python-headless==4.9.0.80", "Installing OpenCV"),
        ("pip install psycopg2-binary==2.9.9", "Installing PostgreSQL connector"),
        ("pip install configparser==5.3.0", "Installing config parser"),
    ]
    
    # Run each command
    for command, description in commands:
        if not run_command(command, description):
            print(f"❌ Build failed at: {description}")
            print("🔧 Trying alternative installation...")
            
            # Try alternative installation for failed package
            if "Pillow" in description:
                run_command("pip install --no-deps --force-reinstall Pillow", "Installing Pillow (alternative)")
            elif "opencv" in description:
                run_command("pip install --no-deps opencv-python-headless==4.9.0.80", "Installing OpenCV (alternative)")
            elif "numpy" in description:
                run_command("pip install --no-deps numpy==1.26.4", "Installing numpy (alternative)")
            else:
                sys.exit(1)
    
    print("✅ All dependencies installed successfully!")
    print("🚀 Ready to start AuraTrack application...")
    
    # Start the application
    try:
        print("🌟 Starting AuraTrack backend...")
        os.system("python clean_backend.py")
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
