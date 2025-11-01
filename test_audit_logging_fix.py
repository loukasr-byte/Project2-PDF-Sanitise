"""
Test script to verify audit logging is working and files are created.
"""
from pathlib import Path
from src.config_manager import ConfigManager
from src.audit_logger import AuditLogger
import shutil
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_audit_logging():
    """Test that audit logs are created in the ./logs folder"""
    
    # Clean up old logs
    logs_dir = Path("logs")
    if logs_dir.exists():
        logger.info(f"Cleaning up old logs directory: {logs_dir}")
        shutil.rmtree(logs_dir)
    
    # Create ConfigManager and get log directory
    config = ConfigManager()
    log_dir = config.get("log_directory")
    logger.info(f"Log directory from config: {log_dir}")
    
    # Create AuditLogger
    logger.info(f"Creating AuditLogger with directory: {log_dir}")
    audit_logger = AuditLogger(log_directory=log_dir)
    
    # Verify directory was created
    log_path = Path(log_dir)
    assert log_path.exists(), f"Log directory not created: {log_path}"
    logger.info(f"✓ Log directory created: {log_path}")
    
    # Create dummy files for testing
    test_orig = Path("test_original.pdf")
    test_sanitized = Path("test_sanitized.pdf")
    test_orig.write_bytes(b"original content")
    test_sanitized.write_bytes(b"sanitized content")
    
    # Log a test event
    test_event = {
        "operator": "test_operator",
        "classification": "TEST",
        "document": {
            "original_name": "test.pdf",
            "original_path": str(test_orig),
            "sanitized_path": str(test_sanitized),
            "processing_time_ms": 1500
        },
        "threats_detected": [
            {
                "type": "TEST_THREAT",
                "severity": "HIGH",
                "action": "REMOVED"
            }
        ],
        "sanitization_policy": "AGGRESSIVE",
        "status": "SUCCESS"
    }
    
    logger.info("Logging test event...")
    audit_logger.log_event(test_event)
    
    # Verify logs were created
    log_files = list(log_path.glob("*.json"))
    assert len(log_files) > 0, "No JSON log files created"
    logger.info(f"✓ JSON log created: {log_files[0].name}")
    
    txt_files = list(log_path.glob("*.txt"))
    assert len(txt_files) > 0, "No TXT log files created"
    logger.info(f"✓ TXT log created: {txt_files[0].name}")
    
    # Read and verify JSON content
    with open(log_files[0], 'r') as f:
        json_content = json.load(f)
    assert json_content.get("status") == "SUCCESS", "JSON log content is invalid"
    logger.info(f"✓ JSON log content verified")
    
    # Read and verify TXT content
    with open(txt_files[0], 'r', encoding='utf-8') as f:
        txt_content = f.read()
    assert "PDF SANITIZATION REPORT" in txt_content, "TXT log content is invalid"
    logger.info(f"✓ TXT log content verified")
    
    # Verify HistoryViewer can read the logs (file-level, not Qt-level)
    logger.info("Testing HistoryViewer log reading capability...")
    log_json_files = sorted(
        audit_logger.log_dir.glob("*.json"),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )
    
    assert len(log_json_files) > 0, "HistoryViewer would not find any logs"
    logger.info(f"✓ HistoryViewer would find {len(log_json_files)} log file(s)")
    
    # Clean up test files
    test_orig.unlink()
    test_sanitized.unlink()
    
    logger.info("\n┌─────────────────────────────────────────┐")
    logger.info("│ ✓ All audit logging tests passed!      │")
    logger.info("│ • Logs created in ./logs folder         │")
    logger.info("│ • Both JSON and TXT formats created     │")
    logger.info("│ • History viewer can read logs          │")
    logger.info("└─────────────────────────────────────────┘")
    return True

if __name__ == "__main__":
    try:
        test_audit_logging()
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        exit(1)
