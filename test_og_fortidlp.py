#!/usr/bin/env python
"""
Test script to process og-fortidlp.pdf and analyze why sanitized file is empty
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config_manager import ConfigManager
from src.sandboxing import SandboxedPDFParser
from src.audit_logger import AuditLogger
from src.queue_manager import QueueManager
from src.core_engine import PDFReconstructor, PDFWhitelistParser
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    pdf_path = "tests/og-fortidlp.pdf"
    
    print("\n" + "="*70)
    print("TESTING og-fortidlp.pdf")
    print("="*70)
    
    # Check file exists and get size
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"[FAIL] File not found: {pdf_path}")
        return
    
    file_size = pdf_file.stat().st_size
    print(f"\n[OK] File found: {pdf_path}")
    print(f"  File size: {file_size} bytes")
    
    # Step 1: Parse the PDF
    print(f"\n[1] Analyzing PDF structure...")
    try:
        import pikepdf
        pdf = pikepdf.Pdf.open(pdf_path)
        print(f"  [OK] PDF opened successfully")
        print(f"  - Pages: {len(pdf.pages)}")
        
        # Check first page
        if len(pdf.pages) > 0:
            page = pdf.pages[0]
            print(f"\n  First page properties:")
            print(f"    - Has Contents: {hasattr(page, 'Contents')}")
            if hasattr(page, 'Contents'):
                contents = page.Contents
                print(f"    - Contents type: {type(contents)}")
                print(f"    - Contents value: {contents}")
                if hasattr(contents, 'read_bytes'):
                    try:
                        data = contents.read_bytes()
                        print(f"    - Content size: {len(data)} bytes")
                        print(f"    - Content preview (first 200 chars): {data[:200]}")
                    except Exception as e:
                        print(f"    - Error reading contents: {e}")
            
            print(f"    - Has MediaBox: {hasattr(page, 'MediaBox')}")
            if hasattr(page, 'MediaBox'):
                print(f"    - MediaBox: {page.MediaBox}")
            
            print(f"    - Has Resources: {hasattr(page, 'Resources')}")
            if hasattr(page, 'Resources'):
                print(f"    - Resources: {page.Resources}")
        
        pdf.close()
    except Exception as e:
        print(f"  [FAIL] Error analyzing PDF: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 2: Parse with whitelist parser
    print(f"\n[2] Running whitelist parser...")
    try:
        parser = PDFWhitelistParser(pdf_path)
        result = parser.parse()
        print(f"  [OK] Parsing complete")
        print(f"  - Pages parsed: {len(result.get('pages', []))}")
        
        for i, page_data in enumerate(result.get('pages', [])):
            print(f"\n  Page {i+1} content:")
            print(f"    - MediaBox: {page_data.get('mediabox')}")
            print(f"    - Contents count: {len(page_data.get('contents', []))}")
            if page_data.get('contents'):
                for j, content in enumerate(page_data['contents']):
                    print(f"    - Content stream {j} size: {len(content)} bytes")
                    print(f"    - Content preview: {content[:100] if len(content) > 100 else content}")
            print(f"    - Resources: {page_data.get('resources')}")
    except Exception as e:
        print(f"  [FAIL] Error during parsing: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 3: Reconstruct PDF
    print(f"\n[3] Reconstructing PDF...")
    try:
        output_path = "tests/og-fortidlp_sanitized.pdf"
        reconstructor = PDFReconstructor(result)
        reconstructor.build(output_path)
        print(f"  [OK] Reconstruction complete")
        
        # Check output file
        output_file = Path(output_path)
        if output_file.exists():
            output_size = output_file.stat().st_size
            print(f"  - Output file size: {output_size} bytes")
            
            # Analyze output PDF
            print(f"\n[4] Analyzing output PDF...")
            output_pdf = pikepdf.Pdf.open(output_path)
            print(f"  - Output pages: {len(output_pdf.pages)}")
            
            if len(output_pdf.pages) > 0:
                out_page = output_pdf.pages[0]
                print(f"  - First page has Contents: {hasattr(out_page, 'Contents')}")
                if hasattr(out_page, 'Contents'):
                    out_contents = out_page.Contents
                    if hasattr(out_contents, 'read_bytes'):
                        out_data = out_contents.read_bytes()
                        print(f"  - Content size: {len(out_data)} bytes")
                        print(f"  - Content preview: {out_data[:200]}")
                    else:
                        print(f"  - Contents: {out_contents}")
            
            output_pdf.close()
        else:
            print(f"  [FAIL] Output file not created")
    except Exception as e:
        print(f"  [FAIL] Error during reconstruction: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
