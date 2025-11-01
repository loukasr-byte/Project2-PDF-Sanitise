#!/usr/bin/env python3
"""
End-to-end test of the PDF sanitization pipeline.
Tests parsing, reconstruction, and audit logging.
"""

import sys
import logging
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_full_pipeline():
    """Test the complete sanitization pipeline."""
    logger.info("=" * 70)
    logger.info("END-TO-END PDF SANITIZATION PIPELINE TEST")
    logger.info("=" * 70)
    
    # Setup
    input_pdf = Path("test_sample.pdf")
    output_pdf = Path("test_sample_sanitized.pdf")
    log_dir = Path("logs")
    
    if not input_pdf.exists():
        logger.error(f"Test PDF not found: {input_pdf}")
        return False
    
    try:
        # Step 1: Initialize components
        logger.info("\n[1] Initializing components...")
        from src.config_manager import ConfigManager
        from src.audit_logger import AuditLogger
        from src.sandboxing import SandboxedPDFParser
        from src.queue_manager import QueueManager
        
        config = ConfigManager()
        audit_logger = AuditLogger(log_directory=str(log_dir))
        parser = SandboxedPDFParser()
        queue_mgr = QueueManager(parser, audit_logger)
        logger.info("    ✓ Components initialized")
        
        # Step 2: Add file to queue
        logger.info("\n[2] Adding PDF to queue...")
        queue_mgr.add_file_to_queue(str(input_pdf))
        logger.info(f"    ✓ Queue size: {len(queue_mgr.queue)}")
        
        # Step 3: Process the queue
        logger.info("\n[3] Processing queue...")
        queue_mgr.process_next_in_queue()
        logger.info(f"    ✓ Queue size after processing: {len(queue_mgr.queue)}")
        
        # Step 4: Verify output file
        logger.info("\n[4] Verifying output file...")
        if not output_pdf.exists():
            logger.error(f"    ✗ Sanitized PDF not created: {output_pdf}")
            return False
        logger.info(f"    ✓ Sanitized PDF created: {output_pdf}")
        logger.info(f"    ✓ File size: {output_pdf.stat().st_size} bytes")
        
        # Step 5: Check audit logs
        logger.info("\n[5] Checking audit logs...")
        log_files = list(log_dir.glob("*.json"))
        if not log_files:
            logger.error("    ✗ No audit logs found")
            return False
        
        latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
        logger.info(f"    ✓ Found {len(log_files)} audit log files")
        logger.info(f"    ✓ Latest log: {latest_log.name}")
        
        # Read the log
        with open(latest_log, 'r') as f:
            log_data = json.load(f)
        logger.info(f"    ✓ Log status: {log_data.get('status')}")
        
        # Step 6: Check TXT logs
        logger.info("\n[6] Checking text audit logs...")
        txt_files = list(log_dir.glob("*.txt"))
        if not txt_files:
            logger.error("    ✗ No text audit logs found")
            return False
        
        latest_txt = max(txt_files, key=lambda p: p.stat().st_mtime)
        logger.info(f"    ✓ Found {len(txt_files)} text audit logs")
        logger.info(f"    ✓ Latest TXT log: {latest_txt.name}")
        
        logger.info("\n" + "=" * 70)
        logger.info("✓ END-TO-END TEST PASSED")
        logger.info("=" * 70)
        logger.info("\nSummary:")
        logger.info(f"  - Input PDF: {input_pdf} ({input_pdf.stat().st_size} bytes)")
        logger.info(f"  - Output PDF: {output_pdf} ({output_pdf.stat().st_size} bytes)")
        logger.info(f"  - Audit logs (JSON): {len(log_files)} files")
        logger.info(f"  - Audit logs (TXT): {len(txt_files)} files")
        logger.info("=" * 70)
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed with exception: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = test_full_pipeline()
    sys.exit(0 if success else 1)
