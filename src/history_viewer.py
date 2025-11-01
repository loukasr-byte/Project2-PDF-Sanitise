from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem

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
        audit log directory.
        """
        log_files = sorted(
            self.audit_logger.log_dir.glob("*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )

        for log_file in log_files:
            item = QListWidgetItem(log_file.name)
            self.history_list_widget.addItem(item)