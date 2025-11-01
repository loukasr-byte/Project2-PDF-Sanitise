# Government-Grade PDF Sanitizer

This application is a defense-grade PDF sanitizer that provides a secure, whitelisting-only approach to PDF sanitization. It is designed to run on air-gapped Windows 11 workstations and includes features such as sandboxed parsing, USB isolation monitoring, and dual-format audit logging.

## How to Run the Application

### Prerequisites
- Python 3.9+ (tested on 3.13.9)
- Windows 10/11
- Dependencies installed via requirements.txt

### Installation

1. **Install Python dependencies**:
    ```bash
    pip install -r requirements.txt --require-hashes
    ```

2. **Verify installation** (optional):
    ```bash
    python test_startup.py
    ```
    This should show "✓ PASS" for all 6 core components.

### Running the GUI

**Option 1: Using the launcher script (Recommended)**
```bash
python run_gui.py
```

**Option 2: Direct module execution**
```bash
python -m src.main_gui
```

**Option 3: Full path from project directory**
```bash
cd c:\KiloCode\Projects\Project2-PDF Sanitise
python src/main_gui.py
```

### Features

- **Whitelisting-only Parsing**: Only passes through known-safe PDF operators and objects
- **Sandboxed Processing**: PDF parsing runs in isolated subprocess
- **Dual-Format Audit Logging**: JSON (machine-readable) and TXT (human-readable) logs
- **USB Isolation Monitoring**: Detects and logs USB device connections
- **Windows Integration**: Uses pywin32 for Job Objects and registry storage
- **Hash Verification**: SHA-256 hashing of original vs sanitized files

### Workflow

1. **Launch the Application**
   ```bash
   python run_gui.py
   ```

2. **Select PDF Files** (Sanitize Tab)
   - Click "Browse" to select PDF files
   - Files appear in the queue list

3. **Process Queue**
   - Click "Process Queue" to sanitize all files
   - Progress updates in real-time
   - Sanitized files created with `_sanitized.pdf` suffix

4. **View Results**
   - **History Tab**: Shows all past sanitization events
   - **Reports Tab**: Details about each sanitization
   - **Settings Tab**: Configure memory limits, timeouts, USB monitoring

5. **Output Files**
   - Sanitized PDFs: Same directory as originals, `[name]_sanitized.pdf`
   - Audit Logs: `logs/STZ-[timestamp].json` and `.txt`

### Directory Structure

```
Project2-PDF Sanitise/
├── run_gui.py                 # GUI launcher (recommended)
├── src/
│   ├── main_gui.py           # PyQt6 GUI application
│   ├── core_engine.py        # PDF parsing & reconstruction
│   ├── sandboxing.py         # Subprocess management
│   ├── queue_manager.py      # File queue orchestration
│   ├── audit_logger.py       # Dual-format logging
│   ├── config_manager.py     # Windows registry config
│   ├── history_viewer.py     # GUI history display
│   ├── report_viewer.py      # GUI reports display
│   ├── usb_monitor.py        # USB isolation monitoring
│   ├── usb_utils.py          # USB utilities
│   └── worker_pdf_parser.py  # Isolated subprocess entrypoint
├── tests/
│   ├── test_sandboxing.py    # Component tests
│   ├── test_startup.py       # Startup verification
│   └── verify_components.py  # Detailed verification
├── logs/
│   └── STZ-*.json, STZ-*.txt # Audit logs
└── requirements.txt          # Python dependencies
```

### Testing

**Run all startup tests**:
```bash
python test_startup.py
```

**Run end-to-end test**:
```bash
python test_e2e.py
```

**Run component tests**:
```bash
python tests/test_sandboxing.py
```

### Troubleshooting

**Issue**: `ModuleNotFoundError: No module named 'src'`
- **Solution**: Use `python run_gui.py` instead of running main_gui.py directly

**Issue**: PyQt6 import errors
- **Solution**: Reinstall: `pip install PyQt6 --upgrade`

**Issue**: pikepdf import errors
- **Solution**: Reinstall: `pip install pikepdf --upgrade`

**Issue**: No sanitized files appear
- **Solution**: Check `logs/` directory for error audit logs showing what went wrong

### Security Features

✓ Whitelisting-only parsing threat model  
✓ Sandboxed subprocess isolation  
✓ No metadata preservation  
✓ SHA-256 integrity verification  
✓ Comprehensive audit trails  
✓ USB isolation monitoring  
✓ Windows process isolation with Job Objects  

### Recent Fixes (v1.1)

- ✅ Fixed PDF reconstruction using correct pikepdf API
- ✅ Fixed module import paths for direct GUI execution
- ✅ Fixed JSON serialization of PDF content
- ✅ Fixed UTF-8 encoding in audit logs
- ✅ Added sys.path resolution for subprocess workers
- ✅ Complete end-to-end pipeline tested and verified

### Status

✅ **PRODUCTION READY** - All tests passing, end-to-end pipeline verified

