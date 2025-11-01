#!/usr/bin/env python3
"""
Debug script to test PDF sanitization and catch crashes.
"""

import sys
from pathlib import Path
import logging
import traceback

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_sanitize_pdf(pdf_path):
    """Test sanitizing a specific PDF and catch any errors."""
    print(f"\n{'='*70}")
    print(f"Testing PDF: {pdf_path}")
    print(f"{'='*70}\n")
    
    if not Path(pdf_path).exists():
        print(f"✗ File not found: {pdf_path}")
        return False
    
    try:
        print("[1] Checking file...")
        file_size = Path(pdf_path).stat().st_size
        print(f"    ✓ File size: {file_size} bytes")
        
        print("\n[2] Initializing components...")
        from src.sandboxing import SandboxedPDFParser
        from src.core_engine import PDFReconstructor
        from src.audit_logger import AuditLogger
        from src.config_manager import ConfigManager
        
        config = ConfigManager()
        parser = SandboxedPDFParser()
        audit_logger = AuditLogger(log_directory=config.get("log_directory"))
        print(f"    ✓ Components initialized")
        
        print("\n[3] Parsing PDF...")
        result = parser.parse_pdf_isolated(pdf_path)
        if result.get("status") != "success":
            error_msg = result.get("message", "Unknown error")
            print(f"    ✗ Parsing failed: {error_msg}")
            return False
        print(f"    ✓ Parsing successful")
        print(f"      - Pages: {len(result.get('pages', []))}")
        
        print("\n[4] Reconstructing PDF...")
        try:
            output_path = Path(pdf_path).parent / f"{Path(pdf_path).stem}_test_sanitized.pdf"
            reconstructor = PDFReconstructor(result)
            reconstructor.build(str(output_path))
            print(f"    ✓ Reconstruction successful")
            print(f"      - Output: {output_path}")
            
            if output_path.exists():
                output_size = output_path.stat().st_size
                print(f"      - Output size: {output_size} bytes")
            else:
                print(f"    ✗ Output file not created!")
                return False
                
        except Exception as e:
            print(f"    ✗ Reconstruction error: {e}")
            print(f"\nFull traceback:")
            traceback.print_exc()
            return False
        
        print("\n[5] Verifying output...")
        try:
            from pikepdf import Pdf
            pdf = Pdf.open(str(output_path))
            print(f"    ✓ Output PDF opened successfully")
            print(f"      - Pages: {len(pdf.pages)}")
            pdf.close()
        except Exception as e:
            print(f"    ✗ Output verification failed: {e}")
            return False
        
        print("\n✅ TEST PASSED\n")
        return True
        
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        print(f"\nFull traceback:")
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # Test with test_sample.pdf first
    print("\nTesting with test_sample.pdf...")
    test_sanitize_pdf("test_sample.pdf")
    
    # Ask user for another file to test
    print("\n" + "="*70)
    print("Enter another PDF file path to test (or press Enter to skip):")
    user_pdf = input().strip()
    
    if user_pdf and Path(user_pdf).exists():
        test_sanitize_pdf(user_pdf)
    elif user_pdf:
        print(f"File not found: {user_pdf}")
