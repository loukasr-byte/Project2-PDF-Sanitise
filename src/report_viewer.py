from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit

class ReportViewer(QWidget):
    """
    A widget to display the sanitization report for a single PDF.
    """
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.report_text_edit = QTextEdit()
        self.report_text_edit.setReadOnly(True)
        self.layout.addWidget(self.report_text_edit)

    def display_report(self, report_data: dict):
        """
        Displays the given report data in a human-readable format.
        """
        # This is a placeholder for a more sophisticated report display.
        # For now, we'll just show the raw JSON.
        import json
        report_str = json.dumps(report_data, indent=2)
        self.report_text_edit.setText(report_str)