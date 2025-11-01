import sys
import logging
from pathlib import Path

# Add parent directory to path to allow 'src' imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QToolBar, QFileDialog, QStatusBar, QLabel, QPushButton, QListWidget,
    QListWidgetItem, QSpinBox, QCheckBox, QFormLayout
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import pyqtSlot, Qt
from src.sandboxing import SandboxedPDFParser
from src.queue_manager import QueueManager
from src.report_viewer import ReportViewer
from src.history_viewer import HistoryViewer
from src.audit_logger import AuditLogger
from src.config_manager import ConfigManager
from src.usb_monitor import USBIsolationMonitor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Government-Grade PDF Sanitizer - Phase 1 (Windows 11)")
        self.setMinimumSize(1000, 700)

        # Initialize core components
        self.config_manager = ConfigManager()
        self.sandboxed_parser = SandboxedPDFParser()
        self.audit_logger = AuditLogger(log_directory=self.config_manager.get("log_directory"))
        self.queue_manager = QueueManager(self.sandboxed_parser, self.audit_logger)
        self.usb_monitor = USBIsolationMonitor()

        # Central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Create UI components
        self._create_menu_bar()
        self._create_tool_bar()
        self._create_tab_widget()
        self._create_status_bar()

        # Connect actions and signals
        self.open_action.triggered.connect(self.open_file_dialog)
        self.exit_action.triggered.connect(self.close)
        self.queue_manager.file_added_to_queue.connect(self.on_file_added)
        self.queue_manager.processing_started.connect(self.on_processing_started)
        self.queue_manager.processing_finished.connect(self.on_processing_finished)
        
        # Start USB isolation monitoring (runs in background)
        self.usb_monitor.start_monitoring()
        logging.info("USB isolation monitoring started")
        
        self.status_bar.showMessage("Ready - USB Isolation Monitoring Active")

    def _create_menu_bar(self):
        self.menu_bar = self.menuBar()
        
        # File Menu
        self.file_menu = self.menu_bar.addMenu("&File")
        self.open_action = QAction("&Open PDF...", self)
        self.open_action.setShortcut("Ctrl+O")
        self.file_menu.addAction(self.open_action)
        self.file_menu.addSeparator()
        self.exit_action = QAction("E&xit", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.file_menu.addAction(self.exit_action)
        
        # Help Menu
        self.help_menu = self.menu_bar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        self.help_menu.addAction(about_action)

    def _create_tool_bar(self):
        self.tool_bar = self.addToolBar("Main Toolbar")
        self.tool_bar.addAction(self.open_action)

    def _create_tab_widget(self):
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        # Sanitize Tab
        self.sanitize_tab = self._create_sanitize_tab()
        
        # History Tab
        self.history_tab = HistoryViewer(self.audit_logger)
        
        # Settings Tab
        self.settings_tab = self._create_settings_tab()
        
        # Reports Tab
        self.reports_tab = ReportViewer()

        self.tab_widget.addTab(self.sanitize_tab, "Sanitize")
        self.tab_widget.addTab(self.history_tab, "History")
        self.tab_widget.addTab(self.settings_tab, "Settings")
        self.tab_widget.addTab(self.reports_tab, "Reports")

    def _create_sanitize_tab(self) -> QWidget:
        """Create the Sanitize tab with file selection and processing."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Instructions label
        instructions = QLabel(
            "Select PDF files to sanitize. PDFs are processed in an isolated "
            "subprocess with strict resource limits and whitelist-only threat model."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # File list
        layout.addWidget(QLabel("Files in Queue:"))
        self.file_list_widget = QListWidget()
        layout.addWidget(self.file_list_widget)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        open_btn = QPushButton("Open PDF")
        open_btn.clicked.connect(self.open_file_dialog)
        button_layout.addWidget(open_btn)
        
        process_btn = QPushButton("Process Queue")
        process_btn.clicked.connect(self.safe_process_queue)
        button_layout.addWidget(process_btn)
        
        clear_btn = QPushButton("Clear Queue")
        clear_btn.clicked.connect(self.safe_clear_queue)
        button_layout.addWidget(clear_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        return widget

    def _create_settings_tab(self) -> QWidget:
        """Create the Settings tab with admin configuration options."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Settings form
        form_layout = QFormLayout()
        
        # Sanitization Policy
        form_layout.addRow(QLabel("Sanitization Policy:"), QLabel(
            self.config_manager.get("sanitization_policy", "AGGRESSIVE")
        ))
        
        # Memory Limit
        memory_spinbox = QSpinBox()
        memory_spinbox.setMinimum(100)
        memory_spinbox.setMaximum(2048)
        memory_spinbox.setValue(self.config_manager.get("memory_limit_mb", 500))
        memory_spinbox.setSuffix(" MB")
        form_layout.addRow("Memory Limit:", memory_spinbox)
        
        # Timeout
        timeout_spinbox = QSpinBox()
        timeout_spinbox.setMinimum(10)
        timeout_spinbox.setMaximum(3600)
        timeout_spinbox.setValue(self.config_manager.get("timeout_seconds", 300))
        timeout_spinbox.setSuffix(" seconds")
        form_layout.addRow("Timeout:", timeout_spinbox)
        
        # USB Monitoring
        usb_checkbox = QCheckBox()
        usb_checkbox.setChecked(self.config_manager.get("enable_usb_isolation_monitoring", True))
        form_layout.addRow("Enable USB Isolation Monitoring:", usb_checkbox)
        
        # Audit Logging
        audit_checkbox = QCheckBox()
        audit_checkbox.setChecked(self.config_manager.get("enable_audit_logging", True))
        form_layout.addRow("Enable Audit Logging:", audit_checkbox)
        
        layout.addLayout(form_layout)
        
        # Info section
        info_label = QLabel(
            "Note: Advanced configuration requires administrator privileges.\n"
            "These settings control PDF processing constraints and security features."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        layout.addStretch()
        
        return widget

    def _create_status_bar(self):
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

    def open_file_dialog(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open PDF File",
            "",
            "PDF Files (*.pdf);;All Files (*)"
        )
        if file_name:
            self.queue_manager.add_file_to_queue(file_name)

    @pyqtSlot(str)
    def on_file_added(self, file_path):
        """Handle file added to queue."""
        self.status_bar.showMessage(f"Added to queue: {file_path}")
        item = QListWidgetItem(file_path)
        self.file_list_widget.addItem(item)
        # Update status with queue size
        queue_size = len(self.queue_manager.queue) if self.queue_manager.queue else 0
        logging.info(f"Queue size: {queue_size}")

    @pyqtSlot(str)
    def on_processing_started(self, file_path):
        """Handle processing started."""
        self.status_bar.showMessage(f"Sanitizing: {file_path}...")

    @pyqtSlot(str, bool, str)
    def on_processing_finished(self, file_path, success, message):
        """Handle processing finished."""
        try:
            # Remove the first item from the file list (corresponds to the processed file)
            if self.file_list_widget.count() > 0:
                self.file_list_widget.takeItem(0)
            
            if success:
                self.status_bar.showMessage(f"✓ Successfully sanitized: {file_path}", 5000)
                # Display report
                report_data = {
                    "status": "success",
                    "original_file": file_path,
                    "sanitized_file": file_path.replace(".pdf", "_sanitized.pdf"),
                    "threats_found": 0
                }
                try:
                    self.reports_tab.display_report(report_data)
                    self.tab_widget.setCurrentWidget(self.reports_tab)
                except Exception as e:
                    logging.warning(f"Could not display report: {e}")
            else:
                error_msg = f"✗ Failed to sanitize: {file_path}"
                if message:
                    error_msg += f"\n{message}"
                self.status_bar.showMessage(f"Failed to sanitize: {file_path}", 5000)
                
                # Show error dialog with details
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    "Sanitization Error",
                    f"Failed to sanitize PDF:\n\n{file_path}\n\nError:\n{message}"
                )
        except Exception as e:
            logging.error(f"Error in on_processing_finished: {e}", exc_info=True)
            self.status_bar.showMessage(f"UI Error: {str(e)}", 5000)

    def _show_about(self):
        """Show about dialog."""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "About Government-Grade PDF Sanitizer",
            "Version 1.0 (Phase 1)\n\n"
            "A defense-grade PDF sanitizer for classified document handling.\n"
            "Whitelisting-only threat model with sandboxed processing.\n\n"
            "© 2025 Kilo Code"
        )

    def safe_process_queue(self):
        """Safely process the queue with error handling."""
        try:
            if self.queue_manager and self.queue_manager.queue and len(self.queue_manager.queue) > 0:
                self.queue_manager.process_next_in_queue()
            else:
                self.status_bar.showMessage("Queue is empty", 3000)
        except Exception as e:
            logging.error(f"Error processing queue: {e}", exc_info=True)
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Processing Error", f"Failed to process queue:\n{str(e)}")

    def safe_clear_queue(self):
        """Safely clear the queue with confirmation."""
        try:
            queue_size = len(self.queue_manager.queue) if self.queue_manager.queue else 0
            if queue_size > 0:
                from PyQt6.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    self,
                    "Clear Queue",
                    f"Clear all {queue_size} file(s) from the queue?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.queue_manager.queue.clear()
                    self.file_list_widget.clear()
                    self.status_bar.showMessage("Queue cleared", 3000)
            else:
                self.status_bar.showMessage("Queue is already empty", 3000)
        except Exception as e:
            logging.error(f"Error clearing queue: {e}", exc_info=True)
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to clear queue:\n{str(e)}")

    def closeEvent(self, event):
        """Handle application close."""
        self.usb_monitor.stop_monitoring()
        logging.info("Application shutting down")
        super().closeEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())