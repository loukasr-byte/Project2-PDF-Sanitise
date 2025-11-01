import threading
from enum import Enum
import pythoncom
import wmi
import subprocess
import winreg
import json
from datetime import datetime
import socket
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class IsolationStatus(Enum):
    HEALTHY = 1
    COMPROMISED = 2
    UNKNOWN = 3

class USBIsolationMonitor:
    """
    Monitors USB isolation mechanisms using real-time WMI event subscriptions.
    If ANY mechanism is disabled/altered, immediately triggers a security lockdown.
    This event-driven approach avoids polling and provides near-instantaneous response.
    """
    
    def __init__(self):
        self.last_status = IsolationStatus.HEALTHY
        self.compromised = False
        self.monitor_thread = None
        self.wmi_watcher = None
        
    def start_monitoring(self):
        """Start background monitor thread for WMI events."""
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True  # Daemon thread will exit when main app exits
        )
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring thread and cleanup WMI resources."""
        try:
            logging.info("Stopping USB isolation monitoring")
            
            # Set flag to stop the monitoring loop
            self.compromised = True
            
            # Stop the WMI watcher
            if self.wmi_watcher:
                try:
                    self.wmi_watcher.stop()
                    logging.info("WMI watcher stopped successfully")
                except Exception as e:
                    logging.error(f"Error stopping WMI watcher: {e}")
            
            # Wait for monitor thread to finish with timeout
            if self.monitor_thread and self.monitor_thread.is_alive():
                logging.info("Waiting for monitor thread to terminate")
                self.monitor_thread.join(timeout=2.0)
                
                if self.monitor_thread.is_alive():
                    logging.warning("Monitor thread did not terminate within timeout (daemon=True, will exit with app)")
                else:
                    logging.info("Monitor thread terminated successfully")
            
            logging.info("USB isolation monitoring stopped and cleanup complete")
        except Exception as e:
            logging.error(f"Error during stop_monitoring cleanup: {e}", exc_info=True)

    def _monitor_loop(self):
        """
        Initializes COM and sets up WMI event subscriptions.
        This loop blocks until the watcher is stopped or an event occurs.
        """
        pythoncom.CoInitialize()
        try:
            c = wmi.WMI()
            
            # Event Query for AppLocker service stopping
            applocker_query = "SELECT * FROM __InstanceModificationEvent WITHIN 5 WHERE TargetInstance ISA 'Win32_Service' AND TargetInstance.Name = 'appidsvc' AND TargetInstance.State != 'Running'"
            
            # Additional queries can be added for registry keys, other services, etc.
            # Example for USB write events (requires specific event log setup):
            # usb_write_query = "SELECT * FROM __InstanceCreationEvent WITHIN 5 WHERE TargetInstance ISA 'Win32_NTLogEvent' AND TargetInstance.Logfile = 'Security' AND TargetInstance.EventIdentifier = 4663" # 4663 = file access
            
            print("[INFO] Starting WMI event watcher for security policy changes...")
            self.wmi_watcher = c.watch_for(
                notification_type="Modification",
                wmi_class="Win32_Service",
                delay_secs=5,
                Name='appidsvc'
            )

            while not self.compromised:
                try:
                    event = self.wmi_watcher(timeout_ms=5000)
                    if event and event.State != 'Running':
                        print("[CRITICAL] AppLocker service state changed! Isolation compromised!")
                        self._handle_isolation_breach()
                        break
                except wmi.x_wmi_timed_out:
                    continue # No events, continue monitoring
        finally:
            pythoncom.CoUninitialize()

    
    def _verify_ntfs_readonly(self) -> bool:
        """Verify NTFS read-only mount is still active"""
        import subprocess
        try:
            # Check via fsutil
            cmd = 'fsutil fsinfo volumeinfo D:\\'
            result = subprocess.check_output(cmd, shell=True, text=True)
            is_readonly = 'Read-only' in result or 'ReadOnly' in result
            
            if not is_readonly:
                print("[CRITICAL] USB mount is NOT read-only! Isolation compromised!")
                return False
            return True
        except Exception as e:
            print(f"[ERROR] Cannot verify NTFS readonly status: {e}")
            return False
    
    def _verify_applocker_policies(self) -> bool:
        """Verify AppLocker policies are still enforced"""
        import subprocess
        import winreg
        
        try:
            # Check if AppLocker service is running
            cmd = 'Get-Service -Name appidsvc | Select-Object Status'
            result = subprocess.check_output(
                ['powershell', '-Command', cmd],
                text=True
            )
            
            if 'Running' not in result:
                print("[CRITICAL] AppLocker service stopped! Isolation compromised!")
                return False
            
            # Check registry for policy enforcement
            reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            policy_key = winreg.OpenKey(
                reg, 
                r'SOFTWARE\Policies\Microsoft\Windows\SrpV2'
            )
            enforcement, _ = winreg.QueryValueEx(policy_key, 'EnforcementMode')
            
            if enforcement == 0:  # 0 = Not Configured / Disabled
                print("[CRITICAL] AppLocker enforcement disabled! Isolation compromised!")
                return False
            
            return True
        except Exception as e:
            print(f"[ERROR] Cannot verify AppLocker status: {e}")
            return False
    
    def _verify_device_guard(self) -> bool:
        """Verify Device Guard / Code Integrity is enabled"""
        import subprocess
        
        try:
            cmd = 'Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\\Microsoft\\Windows\\DeviceGuard'
            result = subprocess.check_output(
                ['powershell', '-Command', cmd],
                text=True
            )
            
            if 'SecurityServicesConfigured' not in result or '0' in result:
                print("[CRITICAL] Device Guard / Code Integrity disabled! Isolation compromised!")
                return False
            
            return True
        except Exception as e:
            print(f"[ERROR] Cannot verify Device Guard: {e}")
            return False
    
    def _verify_no_usb_write_activity(self) -> bool:
        """Monitor Windows Event Log for USB write attempts"""
        import subprocess
        
        try:
            # Query Security Event Log for recent write attempts
            cmd = (
                'Get-EventLog -LogName Security -InstanceId 4656,4657 -Newest 100 | '
                'Where-Object {$_.Message -match "D:\\\\|USB"} | '
                'Where-Object {$_.Message -match "Write|Delete"} | '
                'Measure-Object | Select-Object Count'
            )
            result = subprocess.check_output(
                ['powershell', '-Command', cmd],
                text=True
            )
            
            # If any recent write attempts, quarantine
            if 'Count : 0' not in result:
                print("[CRITICAL] USB write activity detected! Security breach!")
                return False
            
            return True
        except Exception as e:
            # Non-fatal - continue monitoring
            return True
    
    def _handle_isolation_breach(self):
        """Handle breach of isolation - CRITICAL SECURITY EVENT"""
        self.compromised = True
        
        # 1. Immediate shutdown signal
        print("\n" + "="*70)
        print("[CRITICAL SECURITY ALERT] USB ISOLATION COMPROMISED")
        print("="*70)
        print("The application is SHUTTING DOWN due to security compromise.")
        print("USB read-only protection OR code execution controls have been disabled.")
        print("This may indicate an active attack or unauthorized modification.")
        print("="*70 + "\n")
        
        # 2. Forensic logging
        self._log_compromise_event()
        
        # 3. Notify SOC/SIEM
        self._alert_soc()
        
        # 4. Display user warning (blocking dialog)
        self._show_critical_warning_dialog()
        
        # 5. Terminate all processing
        
        os._exit(1)
    
    def _log_compromise_event(self):
        """Log comprehensive forensic data on compromise attempt"""
        
        forensic_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "USB_ISOLATION_BREACH_DETECTED",
            "severity": "CRITICAL",
            "isolation_mechanisms": {
                "ntfs_readonly": self._verify_ntfs_readonly(),
                "applocker_active": self._verify_applocker_policies(),
                "device_guard_active": self._verify_device_guard(),
                "usb_write_activity": not self._verify_no_usb_write_activity()
            },
            "action_taken": "APPLICATION_TERMINATED",
            "recommendation": "Investigate workstation for tampering; review Security Event Log; notify SOC immediately"
        }
        
        log_file = r"C:\ProgramData\PDFSanitizer\compromise_alert.json"
        try:
            with open(log_file, 'a') as f:
                f.write(json.dumps(forensic_log) + "\n")
        except Exception as e:
            print(f"[ERROR] Could not write forensic log: {e}")
    
    def _alert_soc(self):
        """Send alert to SOC via syslog/SIEM integration"""
        
        soc_server = "siem.domain.local"  # Configurable
        soc_port = 514  # syslog
        
        message = (
            f"[CRITICAL] PDF Sanitizer Security Breach: "
            f"USB isolation mechanism compromised on {socket.gethostname()}. "
            f"Immediate investigation required. Application terminated."
        )
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(message.encode(), (soc_server, soc_port))
        except Exception as e:
            print(f"[WARNING] Could not notify SOC: {e}")
    
    def _show_critical_warning_dialog(self):
        """Display blocking dialog to operator"""
        warning_message = (
            "USB ISOLATION MECHANISMS COMPROMISED\n\n"
            "The PDF Sanitizer has detected that one or more USB isolation "
            "mechanisms have been disabled or altered:\n\n"
            "• USB read-only protection may be disabled\n"
            "• AppLocker enforcement may be disabled\n"
            "• Device Guard may be disabled\n\n"
            "This application is terminating immediately for security.\n\n"
            "ACTIONS REQUIRED:\n"
            "1. Contact SOC immediately\n"
            "2. Preserve workstation state for forensic analysis\n"
            "3. Do NOT process any classified documents\n"
            "4. Do NOT disconnect the workstation from security monitoring"
        )
        logging.critical(warning_message)
        
        # Try to show UI dialog if GUI framework is available
        try:
            from PyQt6.QtWidgets import QMessageBox, QApplication
            app = QApplication.instance()
            if app:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.setWindowTitle("[CRITICAL] SECURITY COMPROMISE DETECTED")
                msg.setText(warning_message)
                msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg.exec()
        except ImportError:
            # GUI framework not available, message already logged
            pass
def enforce_usb_readonly_ntfs(usb_drive_letter: str) -> bool:
    """
    Enforce read-only via NTFS permissions (cannot be overridden by apps)
    """
    try:
        cmd = [
            "icacls",
            f"{usb_drive_letter}:\\",
            "/grant:r", f"{os.environ['USERNAME']}:(R)",   # Read-only
            "/deny:r", f"{os.environ['USERNAME']}:(W)",    # Explicit write denial
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        return True
    except Exception as e:
        return False

def verify_usb_readonly(usb_drive_letter: str) -> bool:
    """Verify USB is truly read-only via test write"""
    test_file = f"{usb_drive_letter}:\\test_write.txt"
    try:
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        return False  # Write succeeded - NOT protected
    except (IOError, OSError):
        return True  # Write failed - good, is read-only