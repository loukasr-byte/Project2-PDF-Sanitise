#!/usr/bin/env python
import sys
from pathlib import Path

sys.path.insert(0, '.')
from src.core_engine import PDFWhitelistParser, PDFReconstructor

test_pdfs = [
    'tests/scorereport.pdf',
    'tests/og-fortidlp.pdf',
    'tests/Suggested FortiGate Upgrade Models.pdf',
    'tests/UserGuide-for-Student-Finance.pdf'
]

print("=" * 70)
print("Testing PDF Sanitization Fix")
print("=" * 70)

for test_pdf in test_pdfs:
    pdf_path = Path(test_pdf)
    if not pdf_path.exists():
        print(f"\nSKIPPED (not found): {test_pdf}")
        continue
    
    print(f"\nTesting: {test_pdf}")
    orig_size = pdf_path.stat().st_size
    print(f"  Original size: {orig_size:,} bytes")
    
    try:
        parser = PDFWhitelistParser(test_pdf)
        whitelisted_data = parser.parse()
        num_pages = len(whitelisted_data.get("pages", []))
        print(f"  Parsed pages: {num_pages}")
        
        original_pdf = parser.get_original_pdf()
        output_path = f"{pdf_path.stem}_test_sanitized.pdf"
        
        reconstructor = PDFReconstructor(whitelisted_data, original_pdf)
        reconstructor.build(output_path)
        
        new_size = Path(output_path).stat().st_size
        ratio = new_size / orig_size * 100
        print(f"  Sanitized size: {new_size:,} bytes")
        print(f"  Size ratio: {ratio:.1f}%")
        
        if ratio > 10:  # Reasonable sanitization should preserve most content
            print(f"  [OK] SUCCESS")
        else:
            print(f"  [WARN] Very small sanitized file")
            
    except Exception as e:
        print(f"  [FAIL] ERROR: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)
print("Testing Complete")
print("=" * 70)
