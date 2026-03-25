#!/bin/bash
# Render Build Script for AuraTrack
# This script ensures proper installation of dependencies

echo "🔧 Starting AuraTrack build process..."

# Update pip first
echo "📦 Updating pip..."
python -m pip install --upgrade pip setuptools wheel

# Install core dependencies first
echo "🔨 Installing core dependencies..."
pip install Flask==2.3.3 Flask-CORS==4.0.0

# Install numpy first (required for OpenCV)
echo "🔢 Installing numpy..."
pip install numpy==1.23.5

# Install Pillow with specific flags
echo "🖼️ Installing Pillow..."
pip install --no-cache-dir --force-reinstall Pillow==9.4.0

# Install OpenCV headless
echo "👁️ Installing OpenCV headless..."
pip install opencv-python-headless==4.7.0.72

# Install database connector
echo "🗄️ Installing PostgreSQL connector..."
pip install psycopg2-binary==2.9.6

# Install remaining dependencies
echo "⚙️ Installing remaining dependencies..."
pip install configparser==5.3.0

echo "✅ Build completed successfully!"
echo "🚀 Starting AuraTrack application..."
