#!/usr/bin/env python3
"""
Quick test to verify the fix for empty sanitized PDFs
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core_engine import PDFWhitelistParser, PDFReconstructor
import pikepdf

print("=" * 60)
print("Testing PDF Resource Extraction Fix")
print("=" * 60)

# Test file
test_file = "tests/og-fortidlp.pdf"

if not os.path.exists(test_file):
    print(f"ERROR: Test file not found: {test_file}")
    sys.exit(1)

print(f"\n1. ANALYZING ORIGINAL PDF: {test_file}")
print("-" * 60)
try:
    orig_pdf = pikepdf.Pdf.open(test_file)
    print(f"✓ Original PDF opened successfully")
    print(f"  Pages: {len(orig_pdf.pages)}")
    
    page = orig_pdf.pages[0]
    print(f"\n  Page 1 Properties:")
    print(f"  - MediaBox: {page.MediaBox if hasattr(page, 'MediaBox') else 'N/A'}")
    print(f"  - Has Contents: {hasattr(page, 'Contents')}")
    if hasattr(page, 'Contents') and page.Contents:
        try:
            data = page.Contents.read_bytes()
            print(f"  - Contents size: {len(data)} bytes")
            print(f"  - First 100 chars: {data[:100]}")
        except:
            print(f"  - Could not read Contents")
    
    if hasattr(page, 'Resources') and page.Resources:
        print(f"\n  - Has Resources: Yes")
        if hasattr(page.Resources, 'Font'):
            print(f"    - Fonts: {list(page.Resources.Font.keys())}")
        if hasattr(page.Resources, 'XObject'):
            print(f"    - XObjects: {list(page.Resources.XObject.keys())}")
    
except Exception as e:
    print(f"ERROR reading original PDF: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print(f"\n2. PARSING WITH WHITELIST")
print("-" * 60)
try:
    parser = PDFWhitelistParser(test_file)
    data = parser.parse()
    print(f"✓ Parsing complete")
    print(f"  Pages parsed: {len(data['pages'])}")
    
    if data['pages']:
        page_data = data['pages'][0]
        print(f"\n  Page 1 Data:")
        print(f"  - MediaBox: {page_data['mediabox']}")
        print(f"  - Resources: {page_data['resources']}")
        print(f"  - Contents count: {len(page_data['contents'])}")
        if page_data['contents']:
            print(f"  - First content size: {len(page_data['contents'][0])} chars")
except Exception as e:
    print(f"ERROR in parsing: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print(f"\n3. RECONSTRUCTING PDF")
print("-" * 60)
output_file = "tests/og-fortidlp_sanitized_test.pdf"
try:
    reconstructor = PDFReconstructor(data)
    reconstructor.build(output_file)
    print(f"✓ PDF reconstructed successfully")
    print(f"  Output: {output_file}")
    
    # Check output file
    if os.path.exists(output_file):
        size = os.path.getsize(output_file)
        print(f"  File size: {size} bytes")
except Exception as e:
    print(f"ERROR in reconstruction: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print(f"\n4. ANALYZING SANITIZED PDF")
print("-" * 60)
try:
    san_pdf = pikepdf.Pdf.open(output_file)
    print(f"✓ Sanitized PDF opened successfully")
    print(f"  Pages: {len(san_pdf.pages)}")
    
    page = san_pdf.pages[0]
    print(f"\n  Page 1 Properties:")
    print(f"  - MediaBox: {page.MediaBox if hasattr(page, 'MediaBox') else 'N/A'}")
    print(f"  - Has Contents: {hasattr(page, 'Contents')}")
    if hasattr(page, 'Contents') and page.Contents:
        try:
            data = page.Contents.read_bytes()
            print(f"  - Contents size: {len(data)} bytes")
            print(f"  - First 100 chars: {data[:100]}")
        except:
            print(f"  - Could not read Contents")
    
    if hasattr(page, 'Resources') and page.Resources:
        print(f"\n  - Has Resources: Yes")
        if hasattr(page.Resources, 'Font'):
            fonts = list(page.Resources.Font.keys()) if hasattr(page.Resources.Font, 'keys') else []
            print(f"    - Fonts: {fonts if fonts else '(empty)'}")
        if hasattr(page.Resources, 'XObject'):
            xobjs = list(page.Resources.XObject.keys()) if hasattr(page.Resources.XObject, 'keys') else []
            print(f"    - XObjects: {xobjs if xobjs else '(empty)'}")
    
    print(f"\n✓ RESULT: Sanitized PDF has {'CONTENT' if (hasattr(page, 'Contents') and page.Contents) else 'NO CONTENT'}")
    
except Exception as e:
    print(f"ERROR reading sanitized PDF: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
