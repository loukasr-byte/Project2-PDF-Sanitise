#!/usr/bin/env python3
"""
QUICK START GUIDE - PDF Sanitizer

Run this script to verify the installation and launch the GUI.
"""

import sys
import subprocess
from pathlib import Path

def main():
    print("=" * 70)
    print("PDF SANITIZER - QUICK START GUIDE")
    print("=" * 70)
    print()
    
    # Get project root
    project_root = Path(__file__).parent
    
    print(f"Project directory: {project_root}")
    print()
    
    # Check requirements
    print("1. Checking Python version...")
    if sys.version_info < (3, 9):
        print(f"   ✗ FAIL: Python 3.9+ required, found {sys.version_info.major}.{sys.version_info.minor}")
        return False
    print(f"   ✓ PASS: Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print()
    
    # Check key modules
    print("2. Checking required modules...")
    required_modules = [
        ('PyQt6', 'PyQt6 GUI framework'),
        ('pikepdf', 'PDF processing'),
        ('cryptography', 'Audit logging'),
        ('pywin32', 'Windows integration'),
    ]
    
    all_ok = True
    for module, description in required_modules:
        try:
            __import__(module)
            print(f"   ✓ {module}: {description}")
        except ImportError:
            print(f"   ✗ {module}: NOT INSTALLED ({description})")
            all_ok = False
    print()
    
    if not all_ok:
        print("Missing dependencies! Install with:")
        print(f"  pip install -r requirements.txt")
        print()
        return False
    
    # Run startup test
    print("3. Running component tests...")
    test_file = project_root / "test_startup.py"
    if test_file.exists():
        result = subprocess.run(
            [sys.executable, str(test_file)],
            capture_output=True,
            text=True,
            cwd=str(project_root)
        )
        
        if result.returncode == 0:
            # Count PASS lines
            pass_count = result.stderr.count("✓ PASS")
            print(f"   ✓ All component tests passed ({pass_count}/6)")
        else:
            print("   ✗ Component tests failed")
            return False
    print()
    
    # Ready to launch
    print("=" * 70)
    print("✓ SYSTEM READY - LAUNCHING PDF SANITIZER")
    print("=" * 70)
    print()
    print("The GUI window will open in a new window.")
    print()
    print("What to do:")
    print("  1. Click the 'Sanitize' tab")
    print("  2. Click 'Browse' to select PDF files")
    print("  3. Click 'Process Queue' to sanitize")
    print("  4. Check 'History' tab for results")
    print()
    print("Need help? Check README.md")
    print()
    
    # Launch GUI
    gui_file = project_root / "run_gui.py"
    if gui_file.exists():
        print("Launching GUI...")
        subprocess.run([sys.executable, str(gui_file)], cwd=str(project_root))
    else:
        print("✗ run_gui.py not found!")
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
