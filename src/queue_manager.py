import collections
import logging
import time
from pathlib import Path
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QueueManager(QObject):
    """
    Manages a queue of PDF files to be processed and orchestrates the
    sanitization process for each file.
    """
    # Signals
    file_added_to_queue = pyqtSignal(str)
    processing_started = pyqtSignal(str)
    processing_finished = pyqtSignal(str, bool, str) # filename, success, message

    def __init__(self, sandboxed_parser, audit_logger=None):
        super().__init__()
        self.queue = collections.deque()
        self.sandboxed_parser = sandboxed_parser
        self.audit_logger = audit_logger
        self.processing_count = 0

    def add_file_to_queue(self, file_path: str):
        """Adds a file to the processing queue."""
        file_path = str(file_path)
        logger.info(f"Adding file to queue: {file_path}")
        self.queue.append(file_path)
        self.file_added_to_queue.emit(file_path)

    def process_next_in_queue(self):
        """Processes the next file in the queue."""
        if not self.queue:
            logger.warning("Queue is empty, nothing to process")
            return

        file_path = self.queue[0]  # Peek at the item
        logger.info(f"Processing file: {file_path}")
        self.processing_started.emit(file_path)

        start_time = time.time()
        try:
            # Validate file exists
            if not Path(file_path).exists():
                error_msg = f"File not found: {file_path}"
                logger.error(error_msg)
                self._handle_error(file_path, error_msg, start_time)
                return
            
            # Step 1: Parse PDF
            logger.info(f"Parsing PDF: {file_path}")
            try:
                result = self.sandboxed_parser.parse_pdf_isolated(file_path)
            except Exception as e:
                error_msg = f"Parsing exception: {str(e)}"
                logger.error(error_msg, exc_info=True)
                self._handle_error(file_path, error_msg, start_time)
                return
            
            if result.get("status") != "success":
                error_msg = result.get("message", "Unknown parsing error")
                logger.error(f"Parsing failed: {error_msg}")
                self._handle_error(file_path, error_msg, start_time)
                return

            # Step 2: Reconstruct PDF
            logger.info(f"Reconstructing sanitized PDF")
            try:
                from src.core_engine import PDFReconstructor
                reconstructor = PDFReconstructor(result)
                
                # Generate output path
                input_path = Path(file_path)
                output_path = input_path.parent / f"{input_path.stem}_sanitized.pdf"
                
                logger.info(f"Building sanitized PDF: {output_path}")
                reconstructor.build(str(output_path))
            except Exception as e:
                error_msg = f"Reconstruction exception: {str(e)}"
                logger.error(error_msg, exc_info=True)
                self._handle_error(file_path, error_msg, start_time)
                return
            
            # Verify output file exists
            if not output_path.exists():
                error_msg = f"Sanitized PDF not created at {output_path}"
                logger.error(error_msg)
                self._handle_error(file_path, error_msg, start_time)
                return
            
            processing_time = time.time() - start_time
            
            # Step 3: Log the event
            if self.audit_logger:
                self._log_success(file_path, output_path, result, processing_time)
            
            # Step 4: Emit success signal and remove from queue
            message = f"Sanitization successful. Sanitized file: {output_path}"
            logger.info(message)
            self.queue.popleft()  # Remove only after successful processing
            self.processing_finished.emit(file_path, True, message)
            self.processing_count += 1
            
        except Exception as e:
            logger.exception(f"Unexpected exception during processing: {e}")
            self._handle_error(file_path, str(e), start_time)

    def _handle_error(self, file_path: str, error_msg: str, start_time: float):
        """Handle processing error and log it."""
        processing_time = time.time() - start_time
        
        # Log the error
        if self.audit_logger:
            self._log_error(file_path, error_msg, processing_time)
        
        # Remove from queue and emit error signal
        self.queue.popleft()
        self.processing_finished.emit(file_path, False, f"Error: {error_msg}")

    def _log_success(self, input_file: str, output_file: str, parse_result: dict, processing_time: float):
        """Log successful sanitization to audit logger."""
        try:
            input_path = Path(input_file)
            output_path = Path(output_file)
            
            event_data = {
                "operator": "pdf_sanitizer_system",
                "classification": "UNCLASSIFIED",
                "document": {
                    "original_name": input_path.name,
                    "original_path": str(input_path),
                    "sanitized_path": str(output_path),
                    "processing_time_ms": int(processing_time * 1000)
                },
                "threats_detected": [],
                "sanitization_policy": "AGGRESSIVE",
                "status": "SUCCESS"
            }
            
            self.audit_logger.log_event(event_data)
            logger.info(f"Audit logged for: {input_path.name}")
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")

    def _log_error(self, input_file: str, error_msg: str, processing_time: float):
        """Log processing error to audit logger."""
        try:
            input_path = Path(input_file)
            
            event_data = {
                "operator": "pdf_sanitizer_system",
                "classification": "UNCLASSIFIED",
                "document": {
                    "original_name": input_path.name,
                    "original_path": str(input_path),
                    "processing_time_ms": int(processing_time * 1000)
                },
                "threats_detected": [],
                "sanitization_policy": "AGGRESSIVE",
                "status": "FAILED",
                "error_message": error_msg
            }
            
            self.audit_logger.log_event(event_data)
            logger.info(f"Error logged for: {input_path.name}")
        except Exception as e:
            logger.error(f"Failed to log error audit event: {e}")