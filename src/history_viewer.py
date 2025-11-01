import logging
from pathlib import Path
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class HistoryViewer(QWidget):
    """
    A widget to display a list of past sanitization events.
    """
    def __init__(self, audit_logger):
        super().__init__()
        self.audit_logger = audit_logger
        self.layout = QVBoxLayout(self)
        self.history_list_widget = QListWidget()
        self.layout.addWidget(self.history_list_widget)

        self.populate_history()

    def populate_history(self):
        """
        Populates the history list with past sanitization events from the
        audit log directory. Clears existing items before repopulating.
        """
        logging.info(f"[HISTORY_VIEWER] populate_history called")
        logging.info(f"[HISTORY_VIEWER] Log directory: {self.audit_logger.log_dir}")
        
        # Clear existing items
        self.history_list_widget.clear()
        
        # Verify log directory exists
        if not self.audit_logger.log_dir.exists():
            logging.warning(f"[HISTORY_VIEWER] Log directory does not exist: {self.audit_logger.log_dir}")
            return
        
        log_files = sorted(
            self.audit_logger.log_dir.glob("*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )
        
        logging.info(f"[HISTORY_VIEWER] Found {len(log_files)} log files")

        for log_file in log_files:
            logging.info(f"[HISTORY_VIEWER] Adding log file: {log_file.name}")
            item = QListWidgetItem(log_file.name)
            self.history_list_widget.addItem(item)
    
    def refresh_history(self):
        """
        Refreshes the history display. Called whenever new events are logged.
        """
        logging.info(f"[HISTORY_VIEWER] refresh_history called")
        self.populate_history()
