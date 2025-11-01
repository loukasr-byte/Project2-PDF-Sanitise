#!/usr/bin/env python
"""Regenerate all test sanitized PDFs with the fixed code."""
import sys
from pathlib import Path
import shutil

sys.path.insert(0, '.')
from src.core_engine import PDFWhitelistParser, PDFReconstructor

test_pdfs = [
    'tests/scorereport.pdf',
    'tests/og-fortidlp.pdf',
    'tests/Suggested FortiGate Upgrade Models.pdf',
    'tests/UserGuide-for-Student-Finance.pdf'
]

print("=" * 70)
print("Regenerating Test Sanitized PDFs with Fixed Code")
print("=" * 70)

for test_pdf in test_pdfs:
    pdf_path = Path(test_pdf)
    if not pdf_path.exists():
        print(f"\nSKIPPED (not found): {test_pdf}")
        continue
    
    print(f"\nProcessing: {test_pdf}")
    orig_size = pdf_path.stat().st_size
    
    try:
        parser = PDFWhitelistParser(test_pdf)
        whitelisted_data = parser.parse()
        num_pages = len(whitelisted_data.get("pages", []))
        
        original_pdf = parser.get_original_pdf()
        output_path = f"{pdf_path.stem}_sanitized.pdf"
        
        reconstructor = PDFReconstructor(whitelisted_data, original_pdf)
        reconstructor.build(output_path)
        
        new_size = Path(output_path).stat().st_size
        ratio = new_size / orig_size * 100
        
        print(f"  Original: {orig_size:,} bytes")
        print(f"  Sanitized: {new_size:,} bytes ({ratio:.1f}%)")
        print(f"  Pages: {num_pages}")
        print(f"  [OK]")
            
    except Exception as e:
        print(f"  [FAIL] ERROR: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)
print("Regeneration Complete")
print("=" * 70)
