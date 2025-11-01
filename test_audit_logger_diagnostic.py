#!/usr/bin/env python3
"""
Diagnostic test for audit_logger to verify logs are being created.
"""
import sys
import logging
from pathlib import Path

# Add parent directory to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Configure comprehensive logging to see all messages
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
)

from src.audit_logger import AuditLogger

def test_audit_logger():
    """Test basic audit logger functionality."""
    print("\n" + "="*80)
    print("AUDIT LOGGER DIAGNOSTIC TEST")
    print("="*80 + "\n")
    
    # Create test log directory
    log_dir = Path("diagnostic_logs")
    print(f"1. Creating AuditLogger with log_directory: {log_dir.absolute()}")
    
    try:
        logger = AuditLogger(log_directory=str(log_dir))
        print(f"   [OK] AuditLogger created successfully")
        print(f"   - Log directory: {logger.log_dir}")
        print(f"   - Log directory exists: {logger.log_dir.exists()}")
        print(f"   - Log directory is writable: {logger.log_dir.is_dir()}")
    except Exception as e:
        print(f"   [FAIL] Failed to create AuditLogger: {e}")
        return False
    
    # Create dummy files
    print(f"\n2. Creating test PDF files")
    original_file = Path("diagnostic_original.pdf")
    sanitized_file = Path("diagnostic_sanitized.pdf")
    
    try:
        with open(original_file, "wb") as f:
            f.write(b"original content of a PDF file" * 100)
        with open(sanitized_file, "wb") as f:
            f.write(b"sanitized content")
        print(f"   [OK] Test files created")
        print(f"   - Original: {original_file} ({original_file.stat().st_size} bytes)")
        print(f"   - Sanitized: {sanitized_file} ({sanitized_file.stat().st_size} bytes)")
    except Exception as e:
        print(f"   [FAIL] Failed to create test files: {e}")
        return False
    
    # Log an event
    print(f"\n3. Logging a sanitization event")
    event_data = {
        "operator": "diagnostic_test",
        "classification": "TEST",
        "document": {
            "original_name": "test_document.pdf",
            "original_path": str(original_file.absolute()),
            "sanitized_path": str(sanitized_file.absolute()),
            "processing_time_ms": 1500
        },
        "threats_detected": [
            {
                "type": "TEST_THREAT",
                "severity": "INFO",
                "action": "LOGGED"
            }
        ],
        "sanitization_policy": "AGGRESSIVE",
        "status": "SUCCESS"
    }
    
    try:
        logger.log_event(event_data)
        print(f"   [OK] log_event() called successfully")
    except Exception as e:
        print(f"   [FAIL] Failed to call log_event: {e}", exc_info=True)
        return False
    
    # Verify logs were created
    print(f"\n4. Verifying log files were created")
    json_files = list(log_dir.glob("*.json"))
    txt_files = list(log_dir.glob("*.txt"))
    
    print(f"   - JSON files in {log_dir}: {len(json_files)}")
    for f in json_files:
        print(f"     - {f.name} ({f.stat().st_size} bytes)")
    
    print(f"   - TXT files in {log_dir}: {len(txt_files)}")
    for f in txt_files:
        print(f"     - {f.name} ({f.stat().st_size} bytes)")
    
    if json_files and txt_files:
        print(f"\n   [OK] Log files created successfully!")
        
        # Display content of latest files
        latest_json = max(json_files, key=lambda f: f.stat().st_mtime)
        latest_txt = max(txt_files, key=lambda f: f.stat().st_mtime)
        
        print(f"\n5. Content of latest JSON log ({latest_json.name}):")
        print("   " + "-"*70)
        with open(latest_json, 'r') as f:
            content = f.read()
            for line in content.split('\n')[:20]:  # Show first 20 lines
                print(f"   {line}")
        
        print(f"\n6. Content of latest TXT log ({latest_txt.name}):")
        print("   " + "-"*70)
        with open(latest_txt, 'r') as f:
            content = f.read()
            for line in content.split('\n'):
                print(f"   {line}")
        
        return True
    else:
        print(f"   [FAIL] Log files NOT created!")
        print(f"   - Expected JSON files but found {len(json_files)}")
        print(f"   - Expected TXT files but found {len(txt_files)}")
        return False

if __name__ == '__main__':
    success = test_audit_logger()
    
    print("\n" + "="*80)
    if success:
        print("RESULT: [OK] AUDIT LOGGER WORKING CORRECTLY")
    else:
        print("RESULT: [FAIL] AUDIT LOGGER HAS ISSUES")
    print("="*80 + "\n")
    
    sys.exit(0 if success else 1)
