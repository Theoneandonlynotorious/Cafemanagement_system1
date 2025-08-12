#!/usr/bin/env python3
"""
Setup script for Cafe Management System
This script helps set up the environment and install dependencies
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All packages installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing packages: {e}")
        return False
    return True

def install_zbar():
    """Install zbar library for barcode scanning"""
    print("Installing zbar library for barcode scanning...")
    
    # Try to detect the operating system and provide instructions
    import platform
    os_name = platform.system().lower()
    
    if os_name == "darwin":  # macOS
        print("For macOS, please run: brew install zbar")
        print("If you don't have Homebrew, install it from: https://brew.sh/")
    elif os_name == "linux":
        print("For Ubuntu/Debian, please run: sudo apt-get install libzbar0")
        print("For CentOS/RHEL, please run: sudo yum install zbar")
    elif os_name == "windows":
        print("For Windows:")
        print("1. Download zbar from: https://sourceforge.net/projects/zbar/files/")
        print("2. Install the downloaded package")
        print("3. Add zbar to your system PATH")
    else:
        print(f"Please install zbar library for your operating system: {os_name}")

def create_data_directory():
    """Create necessary directories"""
    print("Creating data directories...")
    os.makedirs("data", exist_ok=True)
    print("✅ Data directory created!")

def main():
    print("🚀 Setting up Cafe Management System...")
    print("=" * 50)
    
    # Install Python requirements
    if not install_requirements():
        return
    
    # Install zbar
    install_zbar()
    
    # Create directories
    create_data_directory()
    
    print("\n" + "=" * 50)
    print("✅ Setup complete!")
    print("\nTo run the application:")
    print("streamlit run cafe_app.py")
    print("\nNote: Make sure zbar library is installed on your system for barcode scanning to work.")

if __name__ == "__main__":
    main()