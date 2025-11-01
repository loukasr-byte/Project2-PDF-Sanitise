#!/usr/bin/env python3
"""
Quick test to verify all core components can be imported and initialized.
"""

import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all required modules can be imported."""
    logger.info("Testing module imports...")
    try:
        from src.config_manager import ConfigManager
        logger.info("✓ ConfigManager imported")
        
        from src.audit_logger import AuditLogger
        logger.info("✓ AuditLogger imported")
        
        from src.sandboxing import SandboxedPDFParser
        logger.info("✓ SandboxedPDFParser imported")
        
        from src.queue_manager import QueueManager
        logger.info("✓ QueueManager imported")
        
        from src.usb_monitor import USBIsolationMonitor
        logger.info("✓ USBIsolationMonitor imported")
        
        from src.core_engine import PDFWhitelistParser, PDFReconstructor
        logger.info("✓ PDFWhitelistParser and PDFReconstructor imported")
        
        return True
    except Exception as e:
        logger.error(f"✗ Import failed: {e}")
        return False

def test_config_manager():
    """Test ConfigManager initialization."""
    logger.info("\nTesting ConfigManager...")
    try:
        from src.config_manager import ConfigManager
        config = ConfigManager()
        logger.info(f"✓ ConfigManager initialized")
        logger.info(f"  - Sanitization policy: {config.get('sanitization_policy')}")
        logger.info(f"  - Memory limit: {config.get('memory_limit_mb')} MB")
        logger.info(f"  - Timeout: {config.get('timeout_seconds')} seconds")
        logger.info(f"  - Config valid: {config.validate_config()}")
        return True
    except Exception as e:
        logger.error(f"✗ ConfigManager test failed: {e}")
        return False

def test_audit_logger():
    """Test AuditLogger initialization."""
    logger.info("\nTesting AuditLogger...")
    try:
        from src.audit_logger import AuditLogger
        audit = AuditLogger(log_directory="logs")
        logger.info(f"✓ AuditLogger initialized")
        logger.info(f"  - Log directory: {audit.log_dir}")
        return True
    except Exception as e:
        logger.error(f"✗ AuditLogger test failed: {e}")
        return False

def test_sandboxing():
    """Test SandboxedPDFParser initialization."""
    logger.info("\nTesting SandboxedPDFParser...")
    try:
        from src.sandboxing import SandboxedPDFParser
        parser = SandboxedPDFParser()
        logger.info(f"✓ SandboxedPDFParser initialized")
        logger.info(f"  - Memory limit: {parser.memory_limit_mb} MB")
        logger.info(f"  - Timeout: {parser.cpu_time_limit_sec} seconds")
        return True
    except Exception as e:
        logger.error(f"✗ SandboxedPDFParser test failed: {e}")
        return False

def test_queue_manager():
    """Test QueueManager initialization."""
    logger.info("\nTesting QueueManager...")
    try:
        from src.sandboxing import SandboxedPDFParser
        from src.queue_manager import QueueManager
        parser = SandboxedPDFParser()
        queue = QueueManager(parser)
        logger.info(f"✓ QueueManager initialized")
        logger.info(f"  - Queue length: {len(queue.queue)}")
        return True
    except Exception as e:
        logger.error(f"✗ QueueManager test failed: {e}")
        return False

def test_core_engine():
    """Test core engine classes."""
    logger.info("\nTesting Core Engine...")
    try:
        from src.core_engine import WHITELISTED_PDF_OBJECTS, WHITELISTED_STREAM_OPERATORS
        logger.info(f"✓ Core engine whitelist definitions loaded")
        logger.info(f"  - Whitelisted PDF objects: {len(WHITELISTED_PDF_OBJECTS)}")
        logger.info(f"  - Whitelisted stream operators: {len(WHITELISTED_STREAM_OPERATORS)}")
        return True
    except Exception as e:
        logger.error(f"✗ Core engine test failed: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("=" * 70)
    logger.info("PDF SANITIZER - COMPONENT STARTUP TEST")
    logger.info("=" * 70)
    
    results = []
    results.append(("Module Imports", test_imports()))
    results.append(("ConfigManager", test_config_manager()))
    results.append(("AuditLogger", test_audit_logger()))
    results.append(("SandboxedPDFParser", test_sandboxing()))
    results.append(("QueueManager", test_queue_manager()))
    results.append(("Core Engine", test_core_engine()))
    
    logger.info("\n" + "=" * 70)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {name}")
    
    logger.info("=" * 70)
    logger.info(f"Total: {passed}/{total} tests passed")
    logger.info("=" * 70)
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
