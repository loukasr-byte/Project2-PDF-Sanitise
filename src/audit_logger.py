"""
Module: audit_logger
Description: Provides a dual-format audit logging system for security and
             compliance. It generates both human-readable text logs and
             structured JSON logs for every sanitization event.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
import socket
import hashlib

# Configure a dedicated logger for audit trails to avoid mixing with app logs
audit_log = logging.getLogger("audit")
audit_log.setLevel(logging.INFO)


class AuditLogger:
    """
    Handles the creation of detailed, dual-format audit logs for each
    PDF sanitization operation.
    """

    def __init__(self, log_directory: str):
        """
        Initializes the logger with a directory to store the logs.
        
        Args:
            log_directory (str): The path to the directory where logs will be saved.
        """
        self.log_dir = Path(log_directory)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        # TODO: Add file handlers to the 'audit_log' logger if needed for separation

    def _generate_hashes(self, file_path: Path) -> tuple[str, int]:
        """Calculates the SHA-256 hash and size of a file."""
        if not file_path.exists():
            return "N/A", 0
        
        hasher = hashlib.sha256()
        size = 0
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
                size += len(chunk)
        return hasher.hexdigest(), size

    def log_event(self, event_data: dict):
        """
        Logs a sanitization event in both TXT and JSON formats.

        Args:
            event_data (dict): A dictionary containing all relevant information
                               about the sanitization event.
        """
        timestamp = datetime.utcnow()
        event_id = f"STZ-{timestamp.strftime('%Y%m%d')}-{timestamp.strftime('%H%M%S%f')[:-3]}"
        
        # Enrich the event data with standard fields
        full_event = {
            "event_id": event_id,
            "timestamp": timestamp.isoformat() + "Z",
            "workstation_id": socket.gethostname(),
            **event_data
        }
        
        # Calculate hashes for original and sanitized files if paths are provided
        if full_event.get("document", {}).get("original_path"):
            path = Path(full_event["document"]["original_path"])
            h, s = self._generate_hashes(path)
            full_event["document"]["original_hash_sha256"] = h
            full_event["document"]["original_size_bytes"] = s

        if full_event.get("document", {}).get("sanitized_path"):
            path = Path(full_event["document"]["sanitized_path"])
            h, s = self._generate_hashes(path)
            full_event["document"]["sanitized_hash_sha256"] = h
            full_event["document"]["sanitized_size_bytes"] = s
            
        self._write_json_log(full_event, event_id)
        self._write_txt_log(full_event, event_id)

    def _write_json_log(self, event: dict, event_id: str):
        """Writes the structured JSON log file."""
        log_file = self.log_dir / f"{event_id}.json"
        try:
            # Create a clean copy for JSON serialization (remove Path objects etc.)
            json_safe_event = json.loads(json.dumps(event, default=str)) 
            with open(log_file, 'w') as f:
                json.dump(json_safe_event, f, indent=2)
            logging.info(f"Successfully wrote JSON audit log: {log_file}")
        except Exception as e:
            logging.error(f"Failed to write JSON audit log {log_file}: {e}")

    def _write_txt_log(self, event: dict, event_id: str):
        """Writes the human-readable text log file."""
        log_file = self.log_dir / f"{event_id}.txt"
        doc = event.get("document", {})
        
        try:
            # Use utf-8 encoding to support special characters
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write("-"*75 + "\n")
                f.write("PDF SANITIZATION REPORT\n")
                f.write(f"Date: {event['timestamp']}\n")
                f.write("-"*75 + "\n")
                f.write(f"Document: {doc.get('original_name', 'N/A')}\n")
                f.write(f"Original Size: {doc.get('original_size_bytes', 0)} bytes\n")
                f.write(f"Sanitized Size: {doc.get('sanitized_size_bytes', 0)} bytes\n")
                f.write(f"Processing Time: {doc.get('processing_time_ms', 0)} ms\n\n")
                
                f.write(f"THREATS DETECTED: {len(event.get('threats_detected', []))} total\n")
                for threat in event.get('threats_detected', []):
                    f.write(f"  [{threat.get('severity', 'UNKNOWN')}] {threat.get('type', 'N/A')}\n")
                    f.write(f"    Action: {threat.get('action', 'N/A')}\n")
                
                status = "SUCCESS" if event.get('status') == "SUCCESS" else "FAILED"
                f.write(f"\nSANITIZATION STATUS: {status}\n")
                f.write(f"Original Hash (SHA-256): {doc.get('original_hash_sha256', 'N/A')}\n")
                f.write(f"Sanitized Hash (SHA-256): {doc.get('sanitized_hash_sha256', 'N/A')}\n")
                f.write("-"*75 + "\n")
                f.write(f"Operator: {event.get('operator', 'N/A')} | Workstation: {event.get('workstation_id', 'N/A')}\n")
            
            logging.info(f"Successfully wrote TXT audit log: {log_file}")
        except Exception as e:
            logging.error(f"Failed to write TXT audit log {log_file}: {e}")

# Example Usage
if __name__ == '__main__':
    # Create dummy files for hash generation
    Path("logs").mkdir(exist_ok=True)
    with open("original.pdf", "wb") as f: f.write(b"original content")
    with open("sanitized.pdf", "wb") as f: f.write(b"sanitized")
    
    logger = AuditLogger(log_directory="logs")
    
    test_event = {
        "operator": "analyst@domain.gov",
        "classification": "TOP_SECRET",
        "document": {
            "original_name": "classified_report.pdf",
            "original_path": "original.pdf",
            "sanitized_path": "sanitized.pdf",
            "processing_time_ms": 1250
        },
        "threats_detected": [
            {
                "type": "EMBEDDED_EXECUTABLE",
                "severity": "CRITICAL",
                "object_id": "23 0",
                "action": "REMOVED"
            },
            {
                "type": "JAVASCRIPT_ACTION",
                "severity": "HIGH",
                "action": "REMOVED"
            }
        ],
        "sanitization_policy": "AGGRESSIVE",
        "status": "SUCCESS"
    }
    
    logger.log_event(test_event)
    print("\nAudit logs generated in the 'logs' directory.")
