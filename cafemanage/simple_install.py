#!/usr/bin/env python3
"""
Simple installation script for Cafe Management System
"""

import subprocess
import sys

def install_packages():
    """Install required packages"""
    packages = [
        'streamlit',
        'qrcode[pil]',
        'pillow'
    ]
    
    print("Installing Cafe Management System packages...")
    print("=" * 50)
    
    for package in packages:
        print(f"Installing {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} installed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error installing {package}: {e}")
            return False
    
    return True

def main():
    print("🚀 Setting up Simple Cafe Management System...")
    print()
    
    if install_packages():
        print("\n" + "=" * 50)
        print("✅ Installation complete!")
        print("\nTo run the application:")
        print("streamlit run cafe_simple.py")
        print("\nNote: This version includes QR code generation but not barcode scanning.")
    else:
        print("❌ Installation failed. Please check the errors above.")

if __name__ == "__main__":
    main()