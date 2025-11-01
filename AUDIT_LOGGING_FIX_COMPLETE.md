# Audit Logging and History Tab Fix - Complete

## Problem Summary
Audit logs were not being created in the `./logs` folder and nothing appeared in the History tab of the application.

## Root Causes Identified

1. **Wrong Default Log Directory Path**
   - `src/config_manager.py` was set to `C:\PDFSanitizer\Logs` instead of `./logs`
   - Application running from project root couldn't access the Windows system directory path

2. **History Viewer Never Refreshed**
   - `src/history_viewer.py` only populated history once on initialization
   - No refresh mechanism existed to reload logs after new events were created
   - History list was never cleared before repopulation

3. **No Signal Connection Between Queue and History**
   - `src/main_gui.py` didn't connect the `processing_finished` signal to history refresh
   - History tab had no way to know when new audit logs were created

## Solutions Applied

### 1. Fixed Log Directory in [`src/config_manager.py`](src/config_manager.py:29)
**Before:**
```python
"log_directory": r"C:\PDFSanitizer\Logs",
```

**After:**
```python
"log_directory": "logs",
```

### 2. Enhanced HistoryViewer in [`src/history_viewer.py`](src/history_viewer.py)
**Changes:**
- Added `logging` import for diagnostic output
- Added `refresh_history()` method that can be called by signals
- Enhanced `populate_history()` to clear existing items before repopulating
- Added directory existence verification with logging
- Added detailed logging for troubleshooting

**Key New Method:**
```python
def refresh_history(self):
    """Refreshes the history display. Called whenever new events are logged."""
    logging.info(f"[HISTORY_VIEWER] refresh_history called")
    self.populate_history()
```

### 3. Connected History Refresh Signal in [`src/main_gui.py`](src/main_gui.py:77)
**Added:**
```python
# Connect to history viewer for refresh after processing
self.queue_manager.processing_finished.connect(self.history_tab.refresh_history)
```

This ensures the History tab automatically refreshes when PDF sanitization completes.

## Verification Results

✅ **All tests passed:**
- Audit logs created in `./logs` folder
- JSON format logs created with full event data
- TXT format logs created with human-readable reports
- History viewer successfully reads and displays logs
- Signal connection established for automatic refresh

### Sample Audit Log (JSON)
```json
{
  "event_id": "STZ-20251101-214127785",
  "timestamp": "2025-11-01T21:41:27.785382Z",
  "workstation_id": "ROSSIDESL",
  "operator": "pdf_sanitizer_system",
  "classification": "UNCLASSIFIED",
  "document": {
    "original_name": "test.pdf",
    "original_path": "test_original.pdf",
    "sanitized_path": "test_sanitized.pdf",
    "processing_time_ms": 1500,
    "original_hash_sha256": "bf573149b23303ca...",
    "original_size_bytes": 16,
    "sanitized_hash_sha256": "7d766008b2e7edc5...",
    "sanitized_size_bytes": 17
  },
  "threats_detected": [
    {
      "type": "TEST_THREAT",
      "severity": "HIGH",
      "action": "REMOVED"
    }
  ],
  "sanitization_policy": "AGGRESSIVE",
  "status": "SUCCESS"
}
```

### Sample Audit Log (TXT)
```
---------------------------------------------------------------------------
PDF SANITIZATION REPORT
Date: 2025-11-01T21:41:27.785382Z
---------------------------------------------------------------------------
Document: test.pdf
Original Size: 16 bytes
Sanitized Size: 17 bytes
Processing Time: 1500 ms

THREATS DETECTED: 1 total
  [HIGH] TEST_THREAT
    Action: REMOVED

SANITIZATION STATUS: SUCCESS
Original Hash (SHA-256): bf573149b23303ca...
Sanitized Hash (SHA-256): 7d766008b2e7edc5...
---------------------------------------------------------------------------
Operator: pdf_sanitizer_system | Workstation: ROSSIDESL
```

## File Changes Summary

| File | Changes |
|------|---------|
| `src/config_manager.py` | Changed default log directory to `"logs"` |
| `src/history_viewer.py` | Added refresh method, logging, and directory validation |
| `src/main_gui.py` | Added signal connection for automatic history refresh |

## How It Works Now

1. **PDF Processing Flow:**
   - User sanitizes PDF through UI
   - Queue manager processes the file
   - Upon completion, calls `_log_success()` or `_log_error()`
   - Audit logger writes JSON and TXT logs to `./logs` directory

2. **History Tab Updates:**
   - `processing_finished` signal emitted by QueueManager
   - MainWindow routes signal to `history_tab.refresh_history()`
   - History viewer clears current list and reloads from `./logs` directory
   - New audit logs immediately appear in History tab

## Testing

Run the verification test:
```bash
python test_audit_logging_fix.py
```

Expected output shows:
- ✓ Log directory created
- ✓ JSON log created
- ✓ TXT log created  
- ✓ Log content verified
- ✓ History viewer can read logs

## Additional Features Added

- **Diagnostic Logging**: All history operations now log to console for debugging
- **Error Handling**: Directory existence checks prevent silent failures
- **Auto-Refresh**: Automatic history update after each sanitization
