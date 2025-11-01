#!/usr/bin/env python
import sys
from pathlib import Path

sys.path.insert(0, '.')
from src.core_engine import PDFWhitelistParser, PDFReconstructor

# Test with first PDF
test_pdf = 'tests/scorereport.pdf'
print(f'Testing with: {test_pdf}')
print(f'Original size: {Path(test_pdf).stat().st_size} bytes')

try:
    parser = PDFWhitelistParser(test_pdf)
    whitelisted_data = parser.parse()
    print(f'Parsed {len(whitelisted_data.get("pages", []))} pages')
    
    original_pdf = parser.get_original_pdf()
    output_path = 'test_output_sanitized.pdf'
    
    reconstructor = PDFReconstructor(whitelisted_data, original_pdf)
    reconstructor.build(output_path)
    
    new_size = Path(output_path).stat().st_size
    print(f'Sanitized size: {new_size} bytes')
    print(f'Size ratio: {new_size / Path(test_pdf).stat().st_size * 100:.1f}%')
    print('SUCCESS!')
except Exception as e:
    print(f'ERROR: {e}')
    import traceback
    traceback.print_exc()
