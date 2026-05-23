#!/usr/bin/env python3
"""
Build script for PingMaster - Creates Windows .exe using PyInstaller
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_build_dirs():
    """Clean previous build directories."""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name}...")
            shutil.rmtree(dir_name)
            print(f"  {dir_name} removed")

def build_exe():
    """Build the .exe using PyInstaller."""
    print("Building PingMaster.exe...")

    # PyInstaller command - use python -m pyinstaller to avoid PATH issues
    # Removed --noconsole so the dashboard is visible
    cmd = [
        sys.executable,
        '-m',
        'PyInstaller',
        '--onefile',
        '--name=PingMaster',
        '--add-data=config.ini;.',
        '--add-data=screenshot.png;.',
        '--icon=NONE',  # Set to icon.ico if you have one
        '--clean',
        'network_monitor.py'
    ]

    try:
        subprocess.run(cmd, check=True)
        print("\n✓ Build successful!")
        print(f"  .exe location: dist/PingMaster.exe")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed: {e}")
        return False

def prepare_release():
    """Prepare release directory with all necessary files."""
    print("\nPreparing release...")
    
    # Create release directory
    release_dir = Path('release')
    release_dir.mkdir(exist_ok=True)
    
    # Copy .exe
    exe_source = Path('dist/PingMaster.exe')
    if exe_source.exists():
        shutil.copy2(exe_source, release_dir / 'PingMaster.exe')
        print(f"  ✓ Copied PingMaster.exe")
    else:
        print(f"  ✗ PingMaster.exe not found in dist/")
        return False
    
    # Copy config.ini
    if Path('config.ini').exists():
        shutil.copy2('config.ini', release_dir / 'config.ini')
        print(f"  ✓ Copied config.ini")
    
    # Copy screenshot.png
    if Path('screenshot.png').exists():
        shutil.copy2('screenshot.png', release_dir / 'screenshot.png')
        print(f"  ✓ Copied screenshot.png")
    
    # Copy README
    if Path('README.md').exists():
        shutil.copy2('README.md', release_dir / 'README.md')
        print(f"  ✓ Copied README.md")
    
    print(f"\n✓ Release prepared in {release_dir}/")
    return True

def main():
    """Main build function."""
    print("=" * 50)
    print("PingMaster Build Script")
    print("=" * 50)
    
    # Check if PyInstaller is installed
    try:
        subprocess.run([sys.executable, '-m', 'PyInstaller', '--version'],
                      capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ PyInstaller not found!")
        print("  Install it with: pip install pyinstaller")
        sys.exit(1)
    
    # Clean previous builds
    clean_build_dirs()
    
    # Build .exe
    if not build_exe():
        sys.exit(1)
    
    # Prepare release
    if not prepare_release():
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("Build complete!")
    print("=" * 50)
    print(f"Release files are in: {Path('release').absolute()}")
    print("\nTo create a zip archive:")
    print("  powershell Compress-Archive -Path release\\* -DestinationPath PingMaster-Windows.zip")

if __name__ == '__main__':
    main()
