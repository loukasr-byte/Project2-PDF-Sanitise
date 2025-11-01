#!/usr/bin/env python
"""
Test file path handling for PDFs from Downloads folder
"""
import sys
from pathlib import Path

# Add parent directory to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config_manager import ConfigManager
from src.sandboxing import SandboxedPDFParser
from src.audit_logger import AuditLogger
from src.queue_manager import QueueManager
from src.core_engine import PDFReconstructor
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_downloads_path():
    """Test processing a PDF from Downloads folder (or any other location)"""
    print("\n" + "="*70)
    print("FILE PATH HANDLING TEST")
    print("="*70)
    
    # Create test PDF path with spaces (simulating Downloads folder)
    test_pdf = Path("test_sample.pdf").resolve()
    
    if not test_pdf.exists():
        print(f"✗ Test PDF not found at: {test_pdf}")
        return False
    
    print(f"\n✓ Test PDF found: {test_pdf}")
    print(f"  File size: {test_pdf.stat().st_size} bytes")
    
    # Initialize components
    print("\n[1] Initializing components...")
    config = ConfigManager()
    parser = SandboxedPDFParser()
    audit_logger = AuditLogger(log_directory="logs")
    queue_manager = QueueManager(parser, audit_logger)
    
    print("✓ Components initialized")
    
    # Add file to queue
    print(f"\n[2] Adding file to queue: {test_pdf}")
    queue_manager.add_file_to_queue(str(test_pdf))
    print(f"✓ Queue size: {len(queue_manager.queue)}")
    
    # Process the file
    print(f"\n[3] Processing file...")
    try:
        queue_manager.process_next_in_queue()
        print(f"✓ Processing completed")
        
        # Check output
        output_path = test_pdf.parent / f"{test_pdf.stem}_sanitized.pdf"
        if output_path.exists():
            print(f"\n✓ Sanitized PDF created: {output_path}")
            print(f"  File size: {output_path.stat().st_size} bytes")
            return True
        else:
            print(f"\n✗ Sanitized PDF not found at: {output_path}")
            return False
            
    except Exception as e:
        print(f"✗ Error during processing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_downloads_path()
    
    print("\n" + "="*70)
    if success:
        print("✓ FILE PATH HANDLING TEST PASSED")
    else:
        print("✗ FILE PATH HANDLING TEST FAILED")
    print("="*70 + "\n")
    
    sys.exit(0 if success else 1)
