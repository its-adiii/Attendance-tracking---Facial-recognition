#!/usr/bin/env python3
"""
Render Python 3.9 Build Script
This script ensures compatibility with Python 3.9
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
    """Main build process for Python 3.9"""
    print("🚀 Starting AuraTrack build for Python 3.9...")
    
    # Check Python version
    python_version = sys.version_info
    print(f"🐍 Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version.major != 3 or python_version.minor != 9:
        print("⚠️ Warning: This script is optimized for Python 3.9")
    
    # Commands to run in order
    commands = [
        ("python -m pip install --upgrade pip setuptools wheel", "Updating pip"),
        ("pip install Flask==2.2.5 Flask-CORS==3.0.10", "Installing Flask"),
        ("pip install numpy==1.21.6", "Installing numpy"),
        ("pip install --no-cache-dir Pillow==8.4.0", "Installing Pillow"),
        ("pip install opencv-python-headless==4.6.0.66", "Installing OpenCV"),
        ("pip install psycopg2-binary==2.9.3", "Installing PostgreSQL connector"),
        ("pip install configparser==5.2.0", "Installing config parser"),
    ]
    
    # Run each command
    for command, description in commands:
        if not run_command(command, description):
            print(f"❌ Build failed at: {description}")
            print("🔧 Trying alternative installation method...")
            
            # Try alternative installation for failed package
            if "Pillow" in description:
                run_command("pip install --no-deps --force-reinstall Pillow==8.4.0", "Installing Pillow (alternative)")
            elif "opencv" in description:
                run_command("pip install --no-deps opencv-python-headless==4.6.0.66", "Installing OpenCV (alternative)")
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
