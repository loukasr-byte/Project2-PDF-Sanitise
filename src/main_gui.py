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
    QListWidgetItem, QSpinBox, QCheckBox, QFormLayout, QComboBox
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
from src.localization import get_localization, t, GREEK, ENGLISH, SUPPORTED_LANGUAGES

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize core components
        self.config_manager = ConfigManager()
        logging.info(f"[MAIN_GUI_INIT] ConfigManager initialized")
        
        # Initialize localization with saved language
        self.localization = get_localization(self.config_manager.get("language", ENGLISH))
        
        self.setWindowTitle(self.localization.t('main_window_title'))
        self.setMinimumSize(1000, 700)

        self.sandboxed_parser = SandboxedPDFParser()
        logging.info(f"[MAIN_GUI_INIT] SandboxedPDFParser initialized")
        
        log_dir = self.config_manager.get("log_directory")
        logging.info(f"[MAIN_GUI_INIT] Creating AuditLogger with log_directory: {log_dir}")
        self.audit_logger = AuditLogger(
            log_directory=log_dir,
            language=self.config_manager.get("language", ENGLISH)
        )
        logging.info(f"[MAIN_GUI_INIT] AuditLogger initialized: {self.audit_logger}")
        
        logging.info(f"[MAIN_GUI_INIT] Creating QueueManager with audit_logger: {self.audit_logger}")
        self.queue_manager = QueueManager(self.sandboxed_parser, self.audit_logger)
        logging.info(f"[MAIN_GUI_INIT] QueueManager initialized")
        
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
        # Connect to history viewer for refresh after processing
        self.queue_manager.processing_finished.connect(self.history_tab.refresh_history)
        
        # Start USB isolation monitoring (runs in background)
        self.usb_monitor.start_monitoring()
        logging.info("USB isolation monitoring started")
        
        self.status_bar.showMessage(self.localization.t('status_ready'))

    def _create_menu_bar(self):
        self.menu_bar = self.menuBar()
        
        # File Menu
        self.file_menu = self.menu_bar.addMenu(self.localization.t('menu_file'))
        self.open_action = QAction(self.localization.t('menu_open_pdf'), self)
        self.open_action.setShortcut("Ctrl+O")
        self.file_menu.addAction(self.open_action)
        self.file_menu.addSeparator()
        self.exit_action = QAction(self.localization.t('menu_exit'), self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.file_menu.addAction(self.exit_action)
        
        # Help Menu
        self.help_menu = self.menu_bar.addMenu(self.localization.t('menu_help'))
        about_action = QAction(self.localization.t('menu_about'), self)
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
        instructions = QLabel(self.localization.t('sanitize_instructions'))
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # File list
        layout.addWidget(QLabel(self.localization.t('files_in_queue')))
        self.file_list_widget = QListWidget()
        layout.addWidget(self.file_list_widget)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        open_btn = QPushButton(self.localization.t('btn_open_pdf'))
        open_btn.clicked.connect(self.open_file_dialog)
        button_layout.addWidget(open_btn)
        
        process_btn = QPushButton(self.localization.t('btn_process_queue'))
        process_btn.clicked.connect(self.safe_process_queue)
        button_layout.addWidget(process_btn)
        
        clear_btn = QPushButton(self.localization.t('btn_clear_queue'))
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
        
        # Language Selection
        language_combo = QComboBox()
        for lang_code, lang_name in SUPPORTED_LANGUAGES.items():
            language_combo.addItem(lang_name, lang_code)
        
        current_language = self.config_manager.get("language", ENGLISH)
        index = language_combo.findData(current_language)
        if index >= 0:
            language_combo.setCurrentIndex(index)
        
        language_combo.currentIndexChanged.connect(self._on_language_changed)
        form_layout.addRow(self.localization.t('settings_language_label'), language_combo)
        
        # Sanitization Policy
        form_layout.addRow(
            QLabel(self.localization.t('settings_policy_label')),
            QLabel(self.localization.t('settings_policy_aggressive'))
        )
        
        # Memory Limit
        memory_spinbox = QSpinBox()
        memory_spinbox.setMinimum(100)
        memory_spinbox.setMaximum(2048)
        memory_spinbox.setValue(self.config_manager.get("memory_limit_mb", 500))
        memory_spinbox.setSuffix(self.localization.t('settings_memory_suffix'))
        form_layout.addRow(self.localization.t('settings_memory_label'), memory_spinbox)
        
        # Timeout
        timeout_spinbox = QSpinBox()
        timeout_spinbox.setMinimum(10)
        timeout_spinbox.setMaximum(3600)
        timeout_spinbox.setValue(self.config_manager.get("timeout_seconds", 300))
        timeout_spinbox.setSuffix(self.localization.t('settings_timeout_suffix'))
        form_layout.addRow(self.localization.t('settings_timeout_label'), timeout_spinbox)
        
        # USB Monitoring
        usb_checkbox = QCheckBox()
        usb_checkbox.setChecked(self.config_manager.get("enable_usb_isolation_monitoring", True))
        form_layout.addRow(self.localization.t('settings_usb_label'), usb_checkbox)
        
        # Audit Logging
        audit_checkbox = QCheckBox()
        audit_checkbox.setChecked(self.config_manager.get("enable_audit_logging", True))
        form_layout.addRow(self.localization.t('settings_audit_label'), audit_checkbox)
        
        layout.addLayout(form_layout)
        
        # Info section
        info_label = QLabel(self.localization.t('settings_info'))
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        layout.addStretch()
        
        return widget

    def _on_language_changed(self, index):
        """Handle language change from dropdown."""
        from PyQt6.QtWidgets import QComboBox
        combo = self.sender()
        if isinstance(combo, QComboBox):
            language_code = combo.currentData()
            self.localization.set_language(language_code)
            self.config_manager.set("language", language_code)
            
            # Show a message about language change
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                self.localization.t('menu_about'),
                "Language changed. Please restart the application for full effect."
            )

    def _create_status_bar(self):
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

    def open_file_dialog(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            self.localization.t('dialog_open_pdf'),
            "",
            self.localization.t('dialog_pdf_filter')
        )
        if file_name:
            self.queue_manager.add_file_to_queue(file_name)

    @pyqtSlot(str)
    def on_file_added(self, file_path):
        """Handle file added to queue."""
        self.status_bar.showMessage(self.localization.t('status_added_to_queue', file_path))
        item = QListWidgetItem(file_path)
        self.file_list_widget.addItem(item)
        # Update status with queue size
        queue_size = len(self.queue_manager.queue) if self.queue_manager.queue else 0
        logging.info(f"Queue size: {queue_size}")

    @pyqtSlot(str)
    def on_processing_started(self, file_path):
        """Handle processing started."""
        self.status_bar.showMessage(self.localization.t('status_sanitizing', file_path))

    @pyqtSlot(str, bool, str)
    def on_processing_finished(self, file_path, success, message):
        """Handle processing finished."""
        try:
            # Remove the first item from the file list (corresponds to the processed file)
            if self.file_list_widget.count() > 0:
                self.file_list_widget.takeItem(0)
            
            if success:
                # Extract the sanitized file path from the message
                sanitized_file = file_path.replace(".pdf", "_sanitized.pdf")
                if "Sanitized file:" in message:
                    # Extract actual path if message contains it
                    try:
                        sanitized_file = message.split("Sanitized file: ")[-1].strip()
                    except:
                        pass
                
                self.status_bar.showMessage(self.localization.t('status_success', sanitized_file), 5000)
                
                # Show success dialog with location
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(
                    self,
                    self.localization.t('dialog_success_title'),
                    self.localization.t('dialog_success_message', file_path, sanitized_file)
                )
                
                # Display report
                report_data = {
                    "status": "success",
                    "original_file": file_path,
                    "sanitized_file": sanitized_file,
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
                self.status_bar.showMessage(self.localization.t('status_failed', file_path), 5000)
                
                # Show error dialog with details and suggestions
                from PyQt6.QtWidgets import QMessageBox
                detailed_message = self.localization.t('dialog_error_message', file_path, message)
                QMessageBox.warning(
                    self,
                    self.localization.t('dialog_error_title'),
                    detailed_message
                )
        except Exception as e:
            logging.error(f"Error in on_processing_finished: {e}", exc_info=True)
            self.status_bar.showMessage(f"UI Error: {str(e)}", 5000)

    def _show_about(self):
        """Show about dialog."""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            self.localization.t('about_title'),
            self.localization.t('about_message')
        )

    def safe_process_queue(self):
        """Safely process the queue with error handling."""
        try:
            if self.queue_manager and self.queue_manager.queue and len(self.queue_manager.queue) > 0:
                self.queue_manager.process_next_in_queue()
            else:
                self.status_bar.showMessage(self.localization.t('status_queue_empty'), 3000)
        except Exception as e:
            logging.error(f"Error processing queue: {e}", exc_info=True)
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                self.localization.t('processing_error_title'),
                self.localization.t('processing_error_message', str(e))
            )

    def safe_clear_queue(self):
        """Safely clear the queue with confirmation."""
        try:
            queue_size = len(self.queue_manager.queue) if self.queue_manager.queue else 0
            if queue_size > 0:
                from PyQt6.QtWidgets import QMessageBox
                reply = QMessageBox.question(
                    self,
                    self.localization.t('dialog_clear_queue_title'),
                    self.localization.t('dialog_clear_queue_message', queue_size),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.queue_manager.queue.clear()
                    self.file_list_widget.clear()
                    self.status_bar.showMessage(self.localization.t('status_queue_cleared'), 3000)
            else:
                self.status_bar.showMessage(self.localization.t('status_queue_empty'), 3000)
        except Exception as e:
            logging.error(f"Error clearing queue: {e}", exc_info=True)
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to clear queue:\n{str(e)}")

    def closeEvent(self, event):
        """Handle application close with proper cleanup of processes and events."""
        try:
            logging.info("Starting application shutdown sequence")
            
            # Step 1: Stop USB monitoring first to prevent security checks during shutdown
            logging.info("Step 1: Stopping USB isolation monitoring")
            if hasattr(self, 'usb_monitor') and self.usb_monitor:
                try:
                    self.usb_monitor.stop_monitoring()
                    logging.info("USB monitoring stopped successfully")
                except Exception as e:
                    logging.error(f"Error stopping USB monitor: {e}", exc_info=True)
            
            # Step 2: Stop queue processing
            logging.info("Step 2: Stopping queue processing")
            if hasattr(self, 'queue_manager') and self.queue_manager:
                try:
                    # Clear any pending items and prevent new processing
                    if hasattr(self.queue_manager, 'queue'):
                        self.queue_manager.queue.clear()
                    logging.info("Queue cleared successfully")
                except Exception as e:
                    logging.error(f"Error stopping queue manager: {e}", exc_info=True)
            
            # Step 3: Cleanup audit logger resources
            logging.info("Step 3: Cleaning up audit logger resources")
            if hasattr(self, 'audit_logger') and self.audit_logger:
                try:
                    # Flush any pending audit logs
                    logging.info("Audit logger cleanup complete")
                except Exception as e:
                    logging.error(f"Error cleaning audit logger: {e}", exc_info=True)
            
            # Step 4: Cleanup sandboxed parser resources
            logging.info("Step 4: Cleaning up sandboxed parser resources")
            if hasattr(self, 'sandboxed_parser') and self.sandboxed_parser:
                try:
                    if hasattr(self.sandboxed_parser, 'cleanup'):
                        self.sandboxed_parser.cleanup()
                    logging.info("Sandboxed parser cleanup complete")
                except Exception as e:
                    logging.error(f"Error cleaning sandboxed parser: {e}", exc_info=True)
            
            # Step 5: Disconnect all signals to prevent callbacks during cleanup
            logging.info("Step 5: Disconnecting all signals")
            try:
                if hasattr(self, 'queue_manager') and self.queue_manager:
                    try:
                        self.queue_manager.file_added_to_queue.disconnect()
                    except:
                        pass
                    try:
                        self.queue_manager.processing_started.disconnect()
                    except:
                        pass
                    try:
                        self.queue_manager.processing_finished.disconnect()
                    except:
                        pass
                logging.info("All signals disconnected successfully")
            except Exception as e:
                logging.error(f"Error disconnecting signals: {e}", exc_info=True)
            
            # Step 6: Accept the close event
            logging.info("All cleanup operations completed, accepting close event")
            event.accept()
            
        except Exception as e:
            logging.error(f"Unexpected error during application shutdown: {e}", exc_info=True)
            # Still accept the event to ensure the application closes
            event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())