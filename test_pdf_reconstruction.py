#!/usr/bin/env python3
"""
Test script to debug PDF reconstruction issues.
Tests with multiple PDFs to identify edge cases.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import logging
from src.sandboxing import SandboxedPDFParser
from src.core_engine import PDFReconstructor
from pikepdf import Pdf

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_pdf_reconstruction(pdf_path):
    """Test PDF reconstruction for a given PDF file."""
    print(f"\n{'='*70}")
    print(f"Testing: {pdf_path}")
    print(f"{'='*70}")
    
    # Check if file exists
    if not Path(pdf_path).exists():
        print(f"✗ File not found: {pdf_path}")
        return False
    
    # Check original PDF structure
    print("\n[1] Checking original PDF structure...")
    try:
        orig_pdf = Pdf.open(pdf_path)
        print(f"   ✓ Original PDF opened successfully")
        print(f"   - Pages: {len(orig_pdf.pages)}")
        print(f"   - Has metadata: {orig_pdf.docinfo is not None}")
        for i, page in enumerate(orig_pdf.pages[:3]):  # Show first 3 pages
            has_contents = hasattr(page, 'Contents') and page.Contents is not None
            has_resources = hasattr(page, 'Resources') and page.Resources is not None
            print(f"   - Page {i}: Contents={has_contents}, Resources={has_resources}")
        orig_pdf.close()
    except Exception as e:
        print(f"   ✗ Error opening original PDF: {e}")
        return False
    
    # Parse PDF
    print("\n[2] Parsing PDF...")
    try:
        parser = SandboxedPDFParser()
        result = parser.parse_pdf_isolated(pdf_path)
        print(f"   ✓ PDF parsed successfully")
        print(f"   - Pages in result: {len(result.get('pages', []))}")
        if result.get('pages'):
            first_page = result['pages'][0]
            print(f"   - First page mediabox: {first_page.get('mediabox')}")
            print(f"   - First page has contents: {len(first_page.get('contents', [])) > 0}")
    except Exception as e:
        print(f"   ✗ Error parsing PDF: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Reconstruct PDF
    print("\n[3] Reconstructing PDF...")
    try:
        output_path = Path(pdf_path).parent / f"{Path(pdf_path).stem}_reconstructed.pdf"
        reconstructor = PDFReconstructor(result)
        reconstructor.build(str(output_path))
        print(f"   ✓ PDF reconstructed successfully")
        print(f"   - Output: {output_path}")
    except Exception as e:
        print(f"   ✗ Error reconstructing PDF: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Verify reconstructed PDF
    print("\n[4] Verifying reconstructed PDF...")
    try:
        reconstructed_pdf = Pdf.open(str(output_path))
        print(f"   ✓ Reconstructed PDF opened successfully")
        print(f"   - Pages: {len(reconstructed_pdf.pages)}")
        print(f"   - Has metadata: {reconstructed_pdf.docinfo is not None}")
        
        # Check page structure
        for i, page in enumerate(reconstructed_pdf.pages[:3]):
            has_contents = hasattr(page, 'Contents') and page.Contents is not None
            has_resources = hasattr(page, 'Resources') and page.Resources is not None
            print(f"   - Page {i}: Contents={has_contents}, Resources={has_resources}")
        
        reconstructed_pdf.close()
        
        # Try opening with other tools
        file_size = output_path.stat().st_size
        print(f"   - File size: {file_size} bytes")
        
        print("\n✓ TEST PASSED")
        return True
        
    except Exception as e:
        print(f"   ✗ Error verifying reconstructed PDF: {e}")
        import traceback
        traceback.print_exc()
        print("\n✗ TEST FAILED")
        return False

if __name__ == '__main__':
    print("\n" + "="*70)
    print("PDF RECONSTRUCTION DEBUGGING TEST")
    print("="*70)
    
    # Test with sample PDF
    test_pdf_reconstruction("test_sample.pdf")
    
    # Test with sanitized PDF if it exists
    if Path("test_sample_sanitized.pdf").exists():
        print("\n\nTrying to open previously sanitized PDF...")
        try:
            pdf = Pdf.open("test_sample_sanitized.pdf")
            print(f"✓ test_sample_sanitized.pdf opens successfully")
            print(f"  Pages: {len(pdf.pages)}")
            pdf.close()
        except Exception as e:
            print(f"✗ test_sample_sanitized.pdf FAILED to open: {e}")
