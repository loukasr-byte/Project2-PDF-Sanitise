#!/usr/bin/env python3
"""
Quick component test without GUI or USB monitoring.
"""

import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("=" * 70)
    logger.info("PDF SANITIZER - COMPONENT VERIFICATION")
    logger.info("=" * 70)
    
    # Test 1: ConfigManager
    try:
        logger.info("\n[1] Testing ConfigManager...")
        from src.config_manager import ConfigManager
        config = ConfigManager()
        assert config.validate_config(), "Config validation failed"
        logger.info(f"    ✓ Config: policy={config.get('sanitization_policy')}, "
                   f"memory={config.get('memory_limit_mb')}MB, "
                   f"timeout={config.get('timeout_seconds')}s")
    except Exception as e:
        logger.error(f"    ✗ ConfigManager failed: {e}")
        return 1
    
    # Test 2: AuditLogger
    try:
        logger.info("\n[2] Testing AuditLogger...")
        from src.audit_logger import AuditLogger
        audit = AuditLogger(log_directory="logs")
        logger.info(f"    ✓ AuditLogger: log_dir={audit.log_dir}")
    except Exception as e:
        logger.error(f"    ✗ AuditLogger failed: {e}")
        return 1
    
    # Test 3: Core Engine
    try:
        logger.info("\n[3] Testing Core Engine...")
        from src.core_engine import WHITELISTED_PDF_OBJECTS, WHITELISTED_STREAM_OPERATORS
        logger.info(f"    ✓ Whitelisted PDF Objects: {len(WHITELISTED_PDF_OBJECTS)} items")
        logger.info(f"    ✓ Whitelisted Stream Operators: {len(WHITELISTED_STREAM_OPERATORS)} items")
    except Exception as e:
        logger.error(f"    ✗ Core Engine failed: {e}")
        return 1
    
    # Test 4: SandboxedPDFParser
    try:
        logger.info("\n[4] Testing SandboxedPDFParser...")
        from src.sandboxing import SandboxedPDFParser
        parser = SandboxedPDFParser()
        logger.info(f"    ✓ SandboxedPDFParser: memory={parser.memory_limit_mb}MB, timeout={parser.cpu_time_limit_sec}s")
    except Exception as e:
        logger.error(f"    ✗ SandboxedPDFParser failed: {e}")
        return 1
    
    # Test 5: QueueManager (without signals)
    try:
        logger.info("\n[5] Testing QueueManager...")
        from src.queue_manager import QueueManager
        from src.sandboxing import SandboxedPDFParser
        parser = SandboxedPDFParser()
        queue_mgr = QueueManager(parser)
        logger.info(f"    ✓ QueueManager: queue size={len(queue_mgr.queue)}")
    except Exception as e:
        logger.error(f"    ✗ QueueManager failed: {e}")
        return 1
    
    # Test 6: USB Utils
    try:
        logger.info("\n[6] Testing USB Utils...")
        from src.usb_utils import is_mount_readonly, read_pdf_from_usb
        logger.info(f"    ✓ USB utils: Functions available")
    except Exception as e:
        logger.error(f"    ✗ USB Utils failed: {e}")
        return 1
    
    logger.info("\n" + "=" * 70)
    logger.info("✓ ALL COMPONENTS VERIFIED SUCCESSFULLY")
    logger.info("=" * 70)
    logger.info("\nApplication is ready for testing!")
    logger.info("Run: python -m src.main_gui  (to start GUI)")
    logger.info("=" * 70)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
