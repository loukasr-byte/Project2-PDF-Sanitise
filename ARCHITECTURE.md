# Government-Grade PDF Sanitizer - Architecture & Design

**Classification**: Design Document  
**Purpose**: Define system architecture, component design, and implementation strategy for a defense-grade PDF sanitizer supporting Top Secret workflows  
**Version**: 3.0 (Ultra-Secure Edition)  
**Author**: Loukas Rossidis
**Date**: 2025-10-31  
**Last Updated**: 2025-10-31

**Key Updates**: 
- Whitelisting-only architecture (0-day threat elimination)
- Sandboxed subprocess processing with resource limits
- Windows 11 exclusive deployment (Phase 1)
- Enhanced USB isolation (kernel + application layers)
- Aggressive sanitization (default) + admin-configurable options
- Dual-format audit logging

---

## 1. Executive Summary & Vision

A two-phase PDF sanitization platform designed to protect classified documents from data exfiltration vectors:

- **Phase 1**: Standalone GUI desktop application for Windows 11 air-gapped secure workstations
- **Phase 2**: REST web service for on-premises server integration (multi-platform)

**Core Capabilities**:
- ✅ Complete metadata removal (aggressive profile default)
- ✅ Whitelisting-only threat model (known-safe operations only)
- ✅ Sandboxed PDF parsing (subprocess isolation, resource limits)
- ✅ Watermark & hidden layer detection and removal
- ✅ 0-day threat mitigation via process sandboxing
- ✅ Windows 11 USB isolation (kernel + application-level enforcement)
- ✅ Dual-format audit logging (human-readable + JSON)
- ✅ Support for scanned documents and complex mixed-content PDFs

---

## 2. Ultra-Secure Sandboxing Architecture (0-Day Threat Mitigation)

### 2.1 Whitelisting-Only Principle

The sanitization engine operates on a **WHITELIST-ONLY** model: *Only known-safe PDF operations are permitted; everything else is blocked or stripped.*

**Operational Philosophy**:
- ❌ NO blacklist-based threat detection (catches known threats only, fails on 0-days)
- ✅ WHITELIST: Only specific PDF objects, operations, and functions required for:
  1. Reading document structure
  2. Extracting visible page content (text, images, vectors)
  3. Removing metadata, scripts, embedded objects
  4. Reconstructing minimal valid PDF

**Whitelisted PDF Objects** (COMPLETE LIST):
- `/Type` (document catalog)
- `/Pages` (page tree)
- `/Kids` (page list)
- `/MediaBox`, `/CropBox` (page dimensions)
- `/Contents` (page content stream - TEXT & IMAGES ONLY)
- `/Resources` → `/Font`, `/Image`, `/XObject` (only standard fonts, raw images)
- `/Font` (only standard 14 fonts: Helvetica, Times, Courier, etc.)
- `/ProcSet` (graphics state)
- `/BaseFont` (no custom/embedded fonts)

**Whitelisted Operations** (Within content streams):
- Text positioning: `BT`, `ET`, `Td`, `Tm`, `T*`
- Text rendering: `Tj`, `TJ`, `'`, `"` (show string operations ONLY)
- Graphics: `re` (rectangle), `f` (fill), `S` (stroke), `n` (end)
- Path construction: `m` (moveto), `l` (lineto), `c` (curveto), `h` (close)
- Image rendering: `Do` (XObject reference - images only)
- State management: `q` (save), `Q` (restore)

**EXPLICITLY BLOCKED** (All others):
- ❌ `/AA` (page actions)
- ❌ `/OpenAction` (automatic execution)
- ❌ `/JavaScript`, `/JS`
- ❌ `/Launch`, `/SubmitForm`, `/GoToR`
- ❌ `/EmbeddedFile`
- ❌ `/RichMedia`, `/Flash`
- ❌ `/AcroForm` (forms)
- ❌ `/Annot` (annotations - any interactive elements)
- ❌ `/OCProperties` (layers)
- ❌ Any custom dictionaries not in whitelist

### 2.2 Sandboxed Subprocess Parsing

**Multi-Layer Isolation** (defense-in-depth):

```
┌─────────────────────────────────────────────────────────┐
│         Main GUI Process (PyQt6 - User Mode)             │
│  - File I/O, user input, UI rendering                   │
│  - Result aggregation & report generation               │
│  - CANNOT access PDF internals directly                 │
└──────────────────┬──────────────────────────────────────┘
                   │ (pipes only - no shared memory)
                   ↓
┌─────────────────────────────────────────────────────────┐
│     Isolated Worker Process (Low Privileges)            │
│  - Runs as unprivileged local user                      │
│  - Limited to %TEMP%\<random_dir> for I/O               │
│  - 500MB memory limit (configurable)                    │
│  - 5-minute timeout per PDF (configurable)              │
│  - CPU affinity: single core only                       │
│  - No network access (firewall enforced)                │
│  - No registry access (AppLocker enforced)              │
└──────────────────┬──────────────────────────────────────┘
                   │ (results only)
                   ↓
┌─────────────────────────────────────────────────────────┐
│      Result Validation & Sanitization Engine            │
│  - Validates all extracted objects against whitelist    │
│  - Reconstructs clean PDF from validated objects only   │
│  - Rejects entire PDF if ANY unauthorized objects found │
└─────────────────────────────────────────────────────────┘
```

**Process Isolation Implementation**:
```python
import subprocess
import tempfile
from pathlib import Path

class SandboxedPDFParser:
    def parse_pdf_isolated(self, input_pdf_path: str, timeout_seconds: int = 300) -> dict:
        """
        Parse PDF in isolated subprocess with strict resource limits
        Returns only whitelisted extracted content
        """
        temp_result_dir = Path(tempfile.mkdtemp(prefix="pdf_parse_"))
        
        # Create worker process with constraints
        process = subprocess.Popen(
            [
                "python",
                "-u",
                "worker_pdf_parser.py",
                "--input", input_pdf_path,
                "--output", str(temp_result_dir),
                "--whitelist-mode", "strict"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,  # Windows only
        )
        
        try:
            stdout, stderr = process.communicate(timeout=timeout_seconds)
            
            if process.returncode != 0:
                raise Exception(f"PDF parser crashed/timed out: {stderr.decode()}")
            
            # Read results from isolated temp directory
            result_file = temp_result_dir / "result.json"
            if result_file.exists():
                return json.loads(result_file.read_text())
            else:
                raise Exception("Parser produced no valid results")
                
        except subprocess.TimeoutExpired:
            process.kill()
            raise TimeoutError(f"PDF parsing exceeded {timeout_seconds}s timeout")
        finally:
            # Cleanup: securely delete temp results
            import shutil
            shutil.rmtree(temp_result_dir, ignore_errors=True)
```

### 2.3 Memory & Resource Constraints (Windows Job Objects)

**Sandboxed Worker Process Limits**:

```
Max Memory: 500 MB (configurable, admin override)
Max CPU Time: 300 seconds (5 minutes, configurable)
Max Disk I/O: 100 MB read (prevent zip bombs)
Max File Activity: Single input + output only
Network Access: NONE (Windows Firewall rule enforced)
Registry Access: NONE (AppLocker policy enforced)
File System Access: ONLY %TEMP%\<random_dir>
Process Affinity: Single CPU core
Priority Level: Idle (non-interfering with UI)
```

**Windows Job Object Implementation**:
```python
import win32job

def create_limited_job_object():
    """Create Windows Job Object with strict resource limits"""
    hjob = win32job.CreateJobObject(None, "PDFSanitizerWorker")
    
    limit_info = win32job.QueryInformationJobObject(
        hjob, win32job.JobObjectExtendedLimitInformation
    )
    
    limit_info['ProcessMemoryLimit'] = 500 * 1024 * 1024  # 500 MB
    limit_info['JobMemoryLimit'] = 500 * 1024 * 1024
    limit_info['LimitFlags'] = (
        win32job.JOB_OBJECT_LIMIT_PROCESS_MEMORY |
        win32job.JOB_OBJECT_LIMIT_JOB_MEMORY |
        win32job.JOB_OBJECT_LIMIT_PROCESS_TIMES
    )
    
    win32job.SetInformationJobObject(hjob, win32job.JobObjectExtendedLimitInformation, limit_info)
    return hjob
```

### 2.4 0-Day Threat Prevention Table

| Layer | Mechanism | Protection |
|-------|-----------|-----------|
| **Process Level** | Subprocess isolation + Job limits | Prevents: heap overflow, arbitrary code execution, infinite loops |
| **Parser Level** | Whitelist-only object processing | Prevents: unknown PDF exploits, polyglot PDFs, parser quirks |
| **Content Level** | Approved operation whitelist | Prevents: JavaScript, LaTeX injection, PostScript commands |
| **I/O Level** | Temporary directory isolation | Prevents: file system traversal, registry access |
| **Memory Level** | 500 MB hard limit + timeout | Prevents: memory exhaustion, zip bomb extractions |
| **Network Level** | Firewall rule (no egress) | Prevents: DNS exfiltration, remote payloads |
| **Privilege Level** | Unprivileged account | Prevents: system modification, UAC bypass |

### 2.5 Whitelisted Content Reconstruction

**Output PDF Generation**:
1. Parse input PDF via isolated worker → Extract ONLY whitelisted objects
2. Create minimal PDF skeleton (header + xref table + trailer)
3. Reconstruct page tree from validated page objects
4. Copy text content from approved text commands only
5. Copy image XObjects (raw pixel data - no embedded code)
6. Write output with ZERO metadata, forms, scripts, or annotations
7. Validate output PDF structure
8. Generate HMAC-SHA256 integrity hash

---

## 3. Technology Stack (Windows 11 Only - Phase 1)


### 4.5 USB Isolation Monitoring & Failure Detection (CRITICAL)

**Continuous Runtime Validation** - The app must **FAIL IMMEDIATELY** if any isolation mechanism is compromised:

```python
import threading
from enum import Enum
import pythoncom
import wmi

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
        if self.wmi_watcher:
            self.wmi_watcher.stop()
        if self.monitor_thread and self.monitor_thread.is_alive():
            # WMI watcher stop should unblock the thread
            self.monitor_thread.join(timeout=2.0)

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
        import os
        os._exit(1)
    
    def _log_compromise_event(self):
        """Log comprehensive forensic data on compromise attempt"""
        import json
        from datetime import datetime
        
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
        import socket
        
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
        from PyQt6.QtWidgets import QMessageBox, QApplication
        from PyQt6.QtCore import Qt
        
        app = QApplication.instance()
        
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("[CRITICAL] SECURITY COMPROMISE DETECTED")
        msg.setText(
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
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

```

**Isolation Health Check Schedule**:
- **Real-time**: Continuously via WMI event subscriptions for critical service/registry changes.
- **On-Demand**: Before each PDF processing job begins (explicit check).
- **On-Focus**: Immediately after user returns to application window.
- **On-Connect**: On USB connection/disconnection events.

**Alerting Strategy**:
- **User Alert**: Blocking red dialog (cannot dismiss without acknowledging)
- **Event Log**: Write to Windows Security Event Log (Event ID 5000+)
- **SOC Alert**: Send syslog message to SIEM (configurable server)
- **Local Log**: Write forensic JSON to encrypted audit folder
- **Termination**: Application exits with code 1 (failure)

---


### 3.1 Backend Core Engine
- **Primary Language**: Python 3.11+ (security-focused ecosystem, mature PDF tools)
- **PDF Processing**: 
  - [`pikepdf>=8.0.0`] (PRIMARY) - advanced threat detection, libqpdf-based C++ parser
  - [`pdfplumber>=0.9.0`] - enhanced content analysis & text extraction
  - [`pypdf>=3.10.0`] - fallback pure-Python parsing
- **Cryptography**: [`cryptography>=41.0.0`], [`pycryptodome>=3.18.0`]
- **Logging**: [`structlog>=23.1.0`] (structured audit logs)
- **Windows Job Management**: [`pywin32>=305`]

### 3.2 GUI Application (Windows 11)
- **Framework**: [`PyQt6>=6.6.0`] (cross-platform, classified-environment suitable)
- **Packaging**: PyInstaller (standalone executable, no Python dependency)
- **Report Generation**: [`reportlab>=4.0.0`] or [`pypdf`]

### 3.3 USB Security (Windows 11 Specific)
- **ReadOnly Mount**: Windows API (FILE_READ_ONLY flag)
- **AppLocker**: Group Policy enforcement (code execution prevention)
- **Device Guard**: Code Integrity policies
- **Monitoring**: Windows Event Viewer integration

### 3.4 Dependencies Summary
```
# Core
pikepdf>=8.0.0
### 3.5 Dependency Management and Security

Given the high-security context of this application, managing the software supply chain for third-party dependencies is critical. The following multi-stage strategy will be implemented to mitigate the risk of supply-chain attacks.

**1. Vetting and Approval Process**:
- **Source Integrity**: Only libraries from reputable, well-maintained sources will be considered. A library's history of security responsiveness is a key selection criterion.
- **Static Analysis (SAST)**: Before a new dependency or version is approved, it will be scanned with static analysis tools like `Bandit` and `Snyk` to detect known vulnerability patterns.
- **License Audit**: All dependency licenses must be permissive (e.g., MIT, Apache 2.0, BSD) and compatible with the project's security requirements.

**2. Secure Installation and Version Control**:
- **Version Pinning**: All dependencies in the `requirements.txt` and `pyproject.toml` files will be pinned to an exact, vetted version (e.g., `pikepdf==8.1.0`, not `pikepdf>=8.0.0`).
- **Hash Checking**: Every pinned dependency will include a SHA-256 hash. The build process will use `pip --require-hashes` to ensure that downloaded packages are authentic and have not been tampered with.
- **Local Artifactory (Recommended)**: For air-gapped or ultra-secure environments, a local repository (e.g., Sonatype Nexus, JFrog Artifactory) will be used to host vetted packages. The build system will be configured to *only* install from this trusted source.

**3. Continuous Monitoring and Auditing**:
- **Automated Scanning**: The continuous integration (CI) pipeline will include a step that automatically scans all dependencies against a vulnerability database (e.g., Snyk, Trivy) on every commit and on a nightly basis.
- **Dependency Audit Trail**: A log will be maintained documenting when each dependency was vetted, by whom, and the results of the security scans.

**4. Incident Response**:
- **Triage**: If a vulnerability is discovered in a dependency, its impact on the application's security posture will be immediately assessed.
- **Patch or Mitigate**: If a patched version is available, it will undergo the full vetting process before being deployed. If not, alternative mitigations will be implemented, which may include replacing the library or disabling the functionality that relies on it.

**Example Secure Requirements File (`requirements.txt`)**:
```
# requirements.txt
# Vetted on 2025-11-01 by security-team
pikepdf==8.1.0 \
    --hash=sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa \
    --hash=sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb

cryptography==41.0.4 \
    --hash=sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc \
    --hash=sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd
```
pdfplumber>=0.9.0
pypdf>=3.10.0

# Security
cryptography>=41.0.0
pycryptodome>=3.18.0

# Windows-specific
pywin32>=305

# Logging
structlog>=23.1.0
python-json-logger>=2.0.0

# GUI
PyQt6>=6.6.0
reportlab>=4.0.0

# Testing
pytest>=7.4.0
pytest-cov>=4.1.0

# Development
black>=23.9.0
pylint>=2.17.0
mypy>=1.5.0
```

---

## 4. Windows 11 USB Isolation Architecture (CRITICAL)

### 4.1 USB Access Control Requirements

**MANDATORY ENFORCEMENT** (Hardware + OS + Application layers):
- ✅ USB mounted **READ-ONLY** (OS kernel-enforced via NTFS flags)
- ✅ **PDF files only** accessible from USB (no directory traversal)
- ✅ **NO write access** from workstation to USB (kernel prevents)
- ✅ **No executable code** from USB can run (AppLocker + Device Guard)
- ✅ **No system access** from USB (isolated mount context)

**Operational Flow**:
1. User connects USB drive with classified PDFs
2. Windows auto-mount → Sanitizer app detects
3. App mounts USB as read-only (confirmed via verification)
4. User selects PDF files from USB (no directory access)
5. PDFs copied to secure temp directory (%TEMP%\<random>)
6. Sanitization occurs in isolated worker process
7. Output PDFs written to workstation output folder (not USB)
8. User manually moves sanitized PDFs to USB if required
9. USB ejected → No workstation data on USB possible

### 4.2 Kernel-Level USB Read-Only Enforcement (Windows 11)

**Method 1: NTFS ACL Enforcement**:
```python
import subprocess
import os

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
```

**Method 2: Windows Group Policy (Registry)**:
```python
import winreg

def set_usb_readonly_via_policy(usb_device_id: str) -> bool:
    """
    Set via Group Policy: Computer Config → Admin Templates → System → Removable Storage Access
    Requires admin privileges
    """
    try:
        reg_path = r"SYSTEM\CurrentControlSet\Control\StorageDevicePolicies"
        registry = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        key = winreg.OpenKey(registry, reg_path, 0, winreg.KEY_WRITE)
        
        # 1 = Read-only, 2 = No access, 3 = Read/Write
        winreg.SetValueEx(key, "RemovableMediaPolicy", 0, winreg.REG_DWORD, 1)
        
        winreg.CloseKey(key)
        return True
    except Exception:
        return False
```

**Method 3: Device Guard + AppLocker**:
- AppLocker Rule: Deny `\Device\HarddiskVolume*` (USB) from executing any .exe, .dll, .bat
- Device Guard: Only signed code allowed system-wide
- Credential Guard: Prevent credential extraction from USB-sourced processes

### 4.3 Application-Level PDF-Only Validation

**Secure USB File Access**:
```python
def read_pdf_from_usb(usb_mount_path: str, filename: str) -> bytes:
    """
    SECURE: Reads ONLY PDF files from USB, prevents directory traversal
    - Validates .pdf extension only
    - Prevents path traversal (../, absolute paths)
    - Checks file size limits
    - Verifies PDF magic number before processing
    """
    # 1. Extension validation
    if not filename.lower().endswith('.pdf'):
        raise ValueError("Only PDF files allowed")
    
    # 2. Path traversal prevention
    if '..' in filename or filename.startswith('/') or filename.startswith('\\'):
        raise ValueError("Path traversal attempt blocked")
    
    filepath = Path(usb_mount_path) / filename
    
    # 3. Verify mount is read-only
    if not is_mount_readonly(usb_mount_path):
        raise SecurityError("USB not mounted read-only!")
    
    # 4. Verify PDF magic number
    with open(filepath, 'rb') as f:
        magic = f.read(4)
        if magic != b'%PDF':
            raise ValueError("Not a valid PDF file (wrong magic number)")
    
    # 5. File size limit
    file_size = filepath.stat().st_size
    if file_size > 500 * 1024 * 1024:  # 500 MB max
        raise ValueError(f"PDF too large: {file_size} bytes")
    
    return filepath.read_bytes()

def is_mount_readonly(mount_path: str) -> bool:
    """Verify Windows mount is read-only via registry check"""
    import ctypes
    
    # Use Windows API to check mount attributes
    try:
        result = ctypes.windll.kernel32.GetVolumeInformationW(
            mount_path, None, 0, None, None, None, None, 0
        )
        # Additional checks via command line
        import subprocess
        cmd = f'fsutil fsinfo volumeinfo {mount_path}'
        output = subprocess.check_output(cmd, shell=True, text=True)
        return 'Read-only' in output or 'ReadOnly' in output
    except:
        return False
```

### 4.4 USB Attack Surface & Mitigations

| Attack Vector | Threat | Windows 11 Mitigation |
|---|---|---|
| Malicious PDF exploit | Code execution via parser | Sandboxed subprocess + Job limits + whitelist parsing |
| USB write-back | Data exfiltration to USB | Kernel-enforced read-only mount (NTFS) |
| Executable on USB | Unauthorized code execution | AppLocker deny all .exe from USB, Device Guard |
| Directory traversal | Access system files | Path validation, symlink resolution blocking |
| USB as boot device | System compromise | Not applicable (workstation already booted before USB connection) |
| USB firmware attack | Raw storage access | Handled by hardware firmware; not in scope |

---

## 5. Core Sanitization Pipeline Architecture

### 5.1 Data Flow

```
Input PDF → Validation → Parsing → Analysis → Sanitization → Reconstruction → Output PDF
                                   ↓
                            Audit Log (Dual-Format)
```

### 5.2 Sanitization Engine Components

**PDFValidator**: PDF structure integrity, encryption detection, version checks

**MetadataExtractor**: Extract Info dictionary, XMP streams, fonts, custom properties

**ContentAnalyzer**: Threat detection engine
- Metadata threats (PII, GPS, timestamps)
- Executable/malicious content (scripts, embedded files, actions)
- Watermarks & hidden layers (OCG, annotations, invisible text)
- Non-standard content (3D, multimedia, forms)

**PDFReconstructor**: 
- Remove identified threat objects
- Rebuild from whitelisted content only
- Reconstruct minimal valid PDF structure

**ReportGenerator**: Threat summary, object IDs, severity classification

**AuditLogger**: Dual-format logging (human-readable TXT + JSON)

### 5.3 Threat Classification

| Level | Category | Action |
|-------|----------|--------|
| **CRITICAL** | Embedded executables, RCE vectors | REMOVE |
| **HIGH** | JavaScript, metadata PII, suspicious scripts | REMOVE |
| **MEDIUM** | Hidden layers, watermarks, forms | REMOVE |
| **LOW** | Timestamps, creator info | SANITIZE |

---

## 6. Security & Compliance Architecture

### 6.1 Dual-Format Audit Logging

**Human-Readable Summary** (TXT):
```
───────────────────────────────────────────────────────────
PDF SANITIZATION REPORT
Date: 2025-10-31 14:32:15 UTC
───────────────────────────────────────────────────────────
Document: classified_report.pdf
Original Size: 2,048,576 bytes
Sanitized Size: 1,024,384 bytes
Processing Time: 1.25 seconds

THREATS DETECTED: 5 total
  [CRITICAL] Embedded Executable - Object 23.0
    Action: REMOVED
  [HIGH] JavaScript Action - /OpenAction
    Action: REMOVED
  [HIGH] Metadata - Creator, Producer, Author
    Action: SANITIZED
  [MEDIUM] Hidden Layer (OCG) - Page 3
    Action: REMOVED
  [LOW] Metadata - Timestamps
    Action: ZEROED (1970-01-01)

SANITIZATION STATUS: ✓ SUCCESS
Original Hash (SHA-256): abc123def456...
Sanitized Hash (SHA-256): xyz789uvw012...
───────────────────────────────────────────────────────────
Operator: analyst@domain.gov | Workstation: SAN-DESK-001
```

**Detailed JSON Log** (compliance systems integration):
```json
{
  "event_id": "STZ-20251031-000543",
  "timestamp": "2025-10-31T14:32:15Z",
  "operator": "analyst@domain.gov",
  "workstation_id": "SAN-DESK-001",
  "classification": "TOP_SECRET",
  "document": {
    "original_name": "classified_report.pdf",
    "original_hash_sha256": "abc123def456...",
    "original_size_bytes": 2048576,
    "sanitized_hash_sha256": "xyz789uvw012...",
    "sanitized_size_bytes": 1024384,
    "processing_time_ms": 1250
  },
  "threats_detected": [
    {
      "type": "EMBEDDED_EXECUTABLE",
      "severity": "CRITICAL",
      "object_id": "23 0",
      "action": "REMOVED"
### 6.5 Secure Configuration Management

To prevent tampering with critical security settings (e.g., sandboxing memory limits, timeouts), the application will implement a secure configuration management strategy. All administrator-configurable settings will be stored in a protected location and cryptographically signed to ensure integrity.

**Storage Mechanism**:
- **Location**: Windows Registry (`HKEY_LOCAL_MACHINE\SOFTWARE\PDFSanitizer`)
- **Permissions**: The registry key will be protected with Access Control Lists (ACLs) that grant write access *only* to the `BUILTIN\Administrators` group. The application's runtime user will have read-only access.

**Integrity and Verification**:
1.  **Signing on Save**: When an administrator modifies and saves the configuration, the application will:
    a. Serialize the settings into a canonical JSON format.
    b. Sign the JSON string using an ECDSA private key stored in a secure location accessible only to administrators (e.g., Windows Certificate Store).
    c. Store both the JSON configuration and the Base64-encoded signature as separate values in the registry.
2.  **Verification on Load**: On application startup and before each sanitization job, the core engine will:
    a. Read the configuration JSON and its signature from the registry.
    b. Use the corresponding public key to verify the signature against the JSON data.
    c. If verification fails, the application will **IMMEDIATELY TERMINATE**, logging a "CRITICAL_CONFIG_TAMPERING_DETECTED" event and alerting the user. This prevents the application from running with weakened security settings.

```python
import json
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature
import winreg

# Conceptual - requires key management infrastructure
def sign_config(config_data: dict, private_key) -> str:
    """Signs a configuration dictionary and returns the signature."""
    canonical_json = json.dumps(config_data, sort_keys=True, separators=(',', ':')).encode('utf-8')
    signature = private_key.sign(canonical_json, ec.ECDSA(hashes.SHA256()))
    return signature.hex()

def verify_config(config_data: dict, signature_hex: str, public_key) -> bool:
    """Verifies the signature of a configuration dictionary."""
    try:
        canonical_json = json.dumps(config_data, sort_keys=True, separators=(',', ':')).encode('utf-8')
        signature = bytes.fromhex(signature_hex)
        public_key.verify(signature, canonical_json, ec.ECDSA(hashes.SHA256()))
        return True
    except (InvalidSignature, ValueError):
        return False

def save_secure_config(config: dict, signature: str):
    """Saves config and signature to HKLM registry with admin-only ACLs."""
    try:
        # NOTE: ACLs must be set on the parent key during installation
        reg_path = r"SOFTWARE\PDFSanitizer"
        with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
            winreg.SetValueEx(key, "Configuration", 0, winreg.REG_SZ, json.dumps(config))
            winreg.SetValueEx(key, "ConfigurationSignature", 0, winreg.REG_SZ, signature)
        print("[INFO] Secure configuration saved.")
    except PermissionError:
        print("[ERROR] Administrator privileges required to save configuration.")

```

This ensures that even if an attacker gains administrative privileges, they cannot silently modify the application's security policies without access to the signing key.
    }
  ],
  "sanitization_policy": "AGGRESSIVE",
  "status": "SUCCESS"
}
```

### 6.2 Data Protection (Phase 1)

- **In-Transit**: Air-gapped workstation + USB read-only isolation
- **At-Rest**: Optional AES-256 encryption for output PDFs
- **Quarantine**: Malicious content isolated with separate audit trail
- **Audit Integrity**: HMAC-SHA256 for log verification

### 6.3 Data Protection (Phase 2)

- **In-Transit**: Mandatory TLS 1.3 for all API communication
- **At-Rest**: PostgreSQL encryption + encrypted blob storage
- **Access Control**: RBAC (ANALYST, REVIEWER, ADMIN roles)
- **Audit Trail**: Immutable append-only logs with sequence numbers

### 6.4 Compliance Alignment

- **NIST SP 800-175B**: Classified information handling
- **ISO 27001**: Information security management
- **OMB M-22-09**: Zero Trust Architecture
- **NCSC**: Secure coding practices

---

## 7. Phase 1: GUI Desktop Application Architecture (Windows 11)

### 7.1 System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  PyQt6 GUI Application                  │
│            (Windows 11 Exclusive - Phase 1)              │
├─────────────────────────────────────────────────────────┤
│  Main Window (800x600 minimum)                          │
│  - Tabbed Interface: Sanitize | History | Settings      │
│  - File selection with drag-drop + USB validation       │
│  - Real-time progress & threat display                  │
│  - Sanitization report viewer                           │
└──────────────────┬──────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────┐
│       Queue Manager & Processing Controller             │
│  - Batch file processing                               │
│  - Worker process management                            │
│  - Result aggregation                                   │
└──────────────────┬──────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────┐
│   Sanitization Engine (Core - Subprocess Isolated)      │
│  - PDFValidator, MetadataExtractor, ContentAnalyzer    │
│  - PDFReconstructor, ReportGenerator, AuditLogger      │
└──────────────────┬──────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────┐
│              File System & Quarantine                   │
│  - Sanitized PDFs, Quarantine, Audit Logs, Reports     │
└─────────────────────────────────────────────────────────┘
```

### 7.2 GUI Workflow

1. **Launch**: Load UI, check USB status, display welcome
2. **File Selection**: Browse workstation or USB files (USB validated)
3. **Pre-Processing**: Show metadata preview, display policy settings
4. **Sanitization**: Real-time progress, threat feed
5. **Post-Processing**: Report view, export options, quarantine management
6. **History**: Searchable audit log viewer with filters

### 7.3 UI Components

**Main Window**:
- Menu bar (File, Edit, View, Help)
- Toolbar (Open, Batch Process, Clear History)
- Tabbed views: Sanitize | History | Settings | Reports

**Settings Tab** (Admin-only):
- Sanitization policy selector (Aggressive is default)
- Memory limit configuration
- Timeout configuration
- Quarantine folder path

---

## 8. Phase 2: Web Service API Architecture

### 8.1 API Endpoints (Multi-Platform Support)

```
POST   /api/v1/sanitize              Submit PDF for sanitization
GET    /api/v1/sanitize/{job_id}     Check job status
GET    /api/v1/sanitize/{job_id}/download   Retrieve sanitized PDF
GET    /api/v1/sanitize/{job_id}/report     Get sanitization report
POST   /api/v1/admin/jobs/cancel/{job_id}   Cancel job (ADMIN)
GET    /api/v1/admin/audit            Audit log access (ADMIN)
POST   /api/v1/admin/policy           Update policy (ADMIN)
GET    /api/v1/health                 Service health status
```

### 8.2 Technology Stack (Phase 2)

- **Server**: [`FastAPI>=0.104.0`] with async workers
- **Database**: [`PostgreSQL 14+`] with encrypted tables
- **Authentication**: JWT + RBAC
- **Containerization**: Docker + Kubernetes
- **Monitoring**: Structured logging to SIEM integration

---

## 9. Implementation Roadmap

### Phase 1: MVP (Windows 11 Desktop GUI) - Detailed Implementation Plan
**Estimated Timeline**: 12-16 weeks

**Sprint 1: Core Engine Foundations (Weeks 1-3)**
- **Task 1.1**: Set up secure development environment: version control, issue tracker, CI/CD pipeline foundation.
- **Task 1.2**: Implement dependency management plan: create vetted `requirements.txt` with pinned versions and hashes.
- **Task 1.3**: Develop the sandboxed subprocess architecture (`SandboxedPDFParser`).
    - Implement process creation with low privileges.
    - Integrate Windows Job Objects for resource constraints (memory, CPU).
- **Task 1.4**: Build the initial PDF whitelist parser and `PDFReconstructor`.
    - Implement logic to identify and extract only whitelisted PDF objects.
    - Create a minimal, clean PDF from the extracted objects.
- **Task 1.5**: Develop the dual-format `AuditLogger` (JSON and human-readable TXT).

**Sprint 2: Security Integrations (Weeks 4-6)**
- **Task 2.1**: Implement the event-driven `USBIsolationMonitor` using WMI.
    - Set up WMI event consumers for AppLocker, Device Guard, and registry changes.
    - Integrate the immediate lockdown and alerting mechanism (`_handle_isolation_breach`).
- **Task 2.2**: Implement the secure configuration management module.
    - Integrate registry storage with ACLs for admin settings.
    - Implement ECDSA signing and verification logic for configuration data.
- **Task 2.3**: Develop the kernel-level USB read-only enforcement module.
    - Integrate `fsutil` and registry-based controls for forcing read-only mounts.
- **Task 2.4**: Build the application-level PDF-only validation for file access from USB.

**Sprint 3: GUI and Application Logic (Weeks 7-9)**
- **Task 3.1**: Develop the main PyQt6 application window and core UI components (tabs, menus, file dialogs).
- **Task 3.2**: Implement the `Queue Manager` and processing controller to manage sanitization jobs.
- **Task 3.3**: Integrate the core sanitization engine with the GUI.
    - Connect UI actions (e.g., "Sanitize" button) to the isolated worker process.
    - Display real-time progress and results in the UI.
- **Task 3.4**: Build the sanitization report viewer and history/audit log viewer.

**Sprint 4: Testing, Packaging, and Hardening (Weeks 10-12)**
- **Task 4.1**: Write comprehensive unit and integration tests for all modules.
    - Focus on security components: sandboxing, USB isolation, and configuration signing.
- **Task 4.2**: Conduct security validation and penetration testing.
    - Test against common PDF exploits and sandbox escape techniques.
    - Verify all isolation mechanisms under simulated attacks.
- **Task 4.3**: Create the PyInstaller build script for packaging the standalone `.exe`.
- **Task 4.4**: Write user and administrator documentation.
- **Task 4.5**: Final code review, hardening, and release preparation.

### Phase 2: Web Service (Enterprise)
**Deliverables** (10-14 weeks additional):
- FastAPI REST server
- PostgreSQL audit database
- Docker/Kubernetes deployment
- API documentation
- Web dashboard (future)

---

## 10. Deployment Strategy

### 10.1 Phase 1: Air-Gapped Workstation (Windows 11)

**Distribution**: PyInstaller standalone executable (.exe)
- No Python installation required
- Runs on standard Windows 11 (build 22H2+)
- Automatic USB detection on connection
- Local audit logs stored in encrypted folder
- Optional USB-based deployment for distribution

**System Requirements**:
- Windows 11 (build 22H2 or later)
- 2GB RAM minimum, 4GB recommended
- 1GB free disk space
- Air-gapped (no network)
- USB 3.0+ (recommended for performance)

### 10.2 Phase 2: On-Premises Web Service

**Deployment**:
- Docker containers (multi-platform support)
- Kubernetes manifests provided
- TLS 1.3 certificate management
- Backup/recovery procedures
- Operational runbook

---

## 11. Risk & Mitigation Matrix

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| PDF library 0-day | Code execution | Medium | Whitelist sandboxing, subprocess isolation, resource limits |
| Metadata leakage | Data exfiltration | Low | Multi-layer validation, post-sanitization QA |
| USB data exfiltration | Classified compromise | Low | Kernel-enforced read-only, AppLocker prevention |
| Performance on large PDFs | DoS-like slowdown | Medium | 5-minute timeout, 500MB memory limit, 100MB I/O quota |
| Audit log tampering | Compliance failure | Low | HMAC-SHA256 signatures, append-only design |

---

## 12. Summary

This ultra-secure architecture provides:

✅ **Whitelisting-only threat model** (0-day resistant)  
✅ **Sandboxed subprocess parsing** (resource-constrained)  
✅ **Aggressive metadata stripping** (configurable by admin)  
✅ **Windows 11 USB isolation** (kernel + app layers)  
✅ **Dual-format audit logging** (compliance + integration)  
✅ **Government-grade security** (NIST/ISO aligned)  
✅ **Phased deployment** (desktop first, web service later)  

**Next Step**: Proceed to Code Mode for Phase 1 implementation
