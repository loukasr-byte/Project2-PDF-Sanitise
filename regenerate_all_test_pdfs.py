"""
Regenerate all test sanitized PDFs using the fixed parser
"""
import os
from pathlib import Path
from src.core_engine import PDFWhitelistParser, PDFReconstructor

test_dir = Path("tests")
test_files = [
    "scorereport.pdf",
    "og-fortidlp.pdf",
    "Suggested FortiGate Upgrade Models.pdf",
    "UserGuide-for-Student-Finance.pdf"
]

print("=" * 70)
print("REGENERATING TEST SANITIZED PDFs WITH FIXED PARSER")
print("=" * 70)

for test_file in test_files:
    input_path = test_dir / test_file
    output_path = test_dir / f"{input_path.stem}_sanitized.pdf"
    
    if not input_path.exists():
        print(f"\n[SKIP] {test_file} - NOT FOUND")
        continue
    
    original_size = os.path.getsize(input_path)
    
    try:
        print(f"\n[PROCESS] {test_file}")
        print(f"   Original size: {original_size:,} bytes")
        
        # Parse with fixed parser
        parser = PDFWhitelistParser(str(input_path))
        whitelisted_data = parser.parse()
        original_pdf = parser.get_original_pdf()
        
        pages_count = len(whitelisted_data.get('pages', []))
        print(f"   Parsed {pages_count} pages")
        
        # Reconstruct
        reconstructor = PDFReconstructor(whitelisted_data, original_pdf)
        reconstructor.build(str(output_path))
        
        sanitized_size = os.path.getsize(output_path)
        percentage = (sanitized_size / original_size * 100)
        
        print(f"   [OK] Sanitized saved: {output_path.name}")
        print(f"   Sanitized size: {sanitized_size:,} bytes ({percentage:.1f}% of original)")
        
    except Exception as e:
        print(f"   [ERROR] {e}")

print("\n" + "=" * 70)
print("REGENERATION COMPLETE")
print("=" * 70)
