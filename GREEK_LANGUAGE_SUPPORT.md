# Greek Language Support for PDF Sanitizer

## Overview

The Government-Grade PDF Sanitizer now includes full localization support with Greek language enabled. Users can switch between English and Greek (Ελληνικά) at any time through the Settings tab.

## Features

### Supported Languages

- **English (en)** - Default language
- **Greek (el)** - Full Greek localization with:
  - All menu items translated
  - All dialog boxes in Greek
  - All status messages in Greek
  - Audit logs support Greek characters (UTF-8 encoded)
  - Settings labels in Greek

### Language Switching

Users can change the application language from the **Settings** tab:

1. Open the application
2. Click the **Settings** tab
3. Select **Language** dropdown
4. Choose from available languages:
   - English
   - Ελληνικά (Greek)
5. Application will save the preference
6. Restart the application for full language change effect

## Technical Implementation

### Localization Module

The localization system is implemented in [`src/localization.py`](src/localization.py):

```python
from src.localization import Localization, t, get_localization, ENGLISH, GREEK
```

#### Key Classes and Functions

- **`Localization` class**: Manages translation strings and language switching
  - `t(key, *args, **kwargs)`: Translate a key to current language with optional formatting
  - `set_language(language_code)`: Change the active language
  - `get_all_keys()`: Get list of all translatable keys

- **Global functions**:
  - `get_localization(language)`: Get the global localization instance
  - `set_language(language_code)`: Set language globally
  - `t(key, *args, **kwargs)`: Convenience function for global translations

### Translation Dictionary Structure

All translations are stored in the `TRANSLATIONS` dictionary organized by UI context:

```python
TRANSLATIONS = {
    'menu_file': {
        'en': '&File',
        'el': '&Αρχείο'
    },
    'btn_open_pdf': {
        'en': 'Open PDF',
        'el': 'Άνοιγμα PDF'
    },
    # ... 35+ translation keys
}
```

### GUI Integration

The main GUI ([`src/main_gui.py`](src/main_gui.py)) uses localization throughout:

```python
from src.localization import get_localization, ENGLISH

# Initialize with saved language
self.localization = get_localization(self.config_manager.get("language", ENGLISH))

# Use translations
self.setWindowTitle(self.localization.t('main_window_title'))
self.btn.setText(self.localization.t('btn_open_pdf'))
```

### Audit Logger Greek Support

The audit logger ([`src/audit_logger.py`](src/audit_logger.py)) supports Greek:

```python
from src.localization import get_localization

# Initialize with language
self.localization = get_localization(language)

# Use in audit messages
self.audit_logger = AuditLogger(
    log_directory=log_dir,
    language=config_manager.get("language", ENGLISH)
)
```

Audit logs are UTF-8 encoded to support Greek characters.

### Configuration Storage

The chosen language is saved in the Windows Registry through [`src/config_manager.py`](src/config_manager.py):

```python
DEFAULT_CONFIG = {
    "language": "en",  # Default language
    # ... other config values
}
```

Language preference persists across application restarts.

## Translation Coverage

The following UI elements are fully translated to Greek:

### Menu Items
- File menu (Open PDF, Exit)
- Help menu (About)

### Tabs
- Sanitize
- History  
- Settings
- Reports

### Buttons
- Open PDF
- Process Queue
- Clear Queue

### Dialogs
- Sanitization success/failure messages
- Error handling and troubleshooting
- Queue management confirmations

### Settings
- Language selector
- Sanitization policy
- Memory limit
- Timeout settings
- USB isolation monitoring
- Audit logging options

### Audit Logging
- PDF opened
- PDF sanitized
- Sanitization failed
- Parsing in progress
- Reconstruction in progress

### Status Messages
- Queue status
- Processing status
- Error messages

## Adding New Languages

To add support for a new language, follow these steps:

### Step 1: Update Localization Module

Edit [`src/localization.py`](src/localization.py):

```python
# Add language code at the top
FRENCH = 'fr'

# Add to SUPPORTED_LANGUAGES
SUPPORTED_LANGUAGES = {
    ENGLISH: 'English',
    GREEK: 'Ελληνικά',
    FRENCH: 'Français'  # New language
}

# Add translations to TRANSLATIONS dictionary
TRANSLATIONS = {
    'main_window_title': {
        ENGLISH: 'Government-Grade PDF Sanitizer - Phase 1 (Windows 11)',
        GREEK: 'Κρατικής Κατηγορίας Αποστείρωση PDF - Φάση 1 (Windows 11)',
        FRENCH: 'Stérilisateur PDF de Grade Gouvernement - Phase 1 (Windows 11)'
    },
    # ... add French translations for all keys
}
```

### Step 2: Update Configuration

Edit [`src/config_manager.py`](src/config_manager.py) to accept the new language code in validation if needed.

### Step 3: Test

Run the localization tests:

```bash
python test_greek_localization.py
```

Verify the new language appears in the Settings tab dropdown.

## Files Modified for Greek Support

1. **[`src/localization.py`](src/localization.py)** (NEW)
   - Complete localization system with Greek translations
   - 35+ translation keys covering entire UI

2. **[`src/main_gui.py`](src/main_gui.py)** (MODIFIED)
   - Initialize localization with saved language
   - Use localized strings throughout GUI
   - Add language selector to Settings tab
   - Handle language change events

3. **[`src/config_manager.py`](src/config_manager.py)** (MODIFIED)
   - Added `language` key to `DEFAULT_CONFIG`
   - Language preference stored in Windows Registry

4. **[`src/audit_logger.py`](src/audit_logger.py)** (MODIFIED)
   - Accept language parameter in constructor
   - Support UTF-8 encoding for Greek characters in audit logs

5. **[`test_greek_localization.py`](test_greek_localization.py)** (NEW)
   - Comprehensive test suite for localization
   - Tests English/Greek translations
   - Tests language switching
   - Tests string formatting
   - 9 test functions covering all functionality

## Testing Greek Language Support

A complete test suite is available:

```bash
python test_greek_localization.py
```

Test coverage includes:
- Supported languages detection
- English localization completeness
- Greek localization completeness
- Dialog message formatting
- Language switching functionality
- Global localization functions
- String formatting with variables
- Audit log translation keys
- Translation key coverage (35+ keys)

All tests should pass with the message:
```
[SUCCESS] All tests passed! Greek language support is functional.
```

## Usage Examples

### Using Greek in the GUI

1. Start the application:
   ```bash
   python run_gui.py
   ```

2. Go to Settings tab

3. Select "Ελληνικά" from Language dropdown

4. Restart application for full effect

### Programmatic Language Control

```python
from src.localization import Localization, GREEK, ENGLISH

# Create Greek localization instance
loc_greek = Localization(GREEK)
message = loc_greek.t('dialog_success_title')  # Returns: "Επιτυχία Αποστείρωσης"

# Switch languages
loc_greek.set_language(ENGLISH)
message = loc_greek.t('dialog_success_title')  # Returns: "Sanitization Success"

# Use global functions
from src.localization import set_language, t
set_language(GREEK)
message = t('btn_open_pdf')  # Returns: "Άνοιγμα PDF"
```

### In Audit Logs

Audit logs include audit event messages in the selected language:

```
Date: 2025-11-01T20:38:10Z
Document: classified_report.pdf
THREATS DETECTED: 0 total

SANITIZATION STATUS: SUCCESS
...
```

Messages are UTF-8 encoded, supporting Greek characters:
```
Το αρχείο PDF αποστειρώθηκε  (Greek: "The PDF file was sanitized")
```

## Technical Details

### UTF-8 Encoding

- All Greek text is stored in UTF-8 format
- Audit logs use `encoding='utf-8'` when writing files
- GUI properly handles Unicode Greek characters through PyQt6
- Windows file system supports Unicode filenames

### Language Fallback

If a translation key is missing for the selected language, the system automatically falls back to English.

### Performance

- Language switching is instant (no file I/O)
- Translation lookup is O(1) dictionary access
- Minimal memory overhead (~50KB for all translations)

### Compatibility

- Python 3.9+ (tested on 3.13.9)
- Windows 10/11
- PyQt6 framework
- UTF-8 compatible file systems

## Known Limitations

1. Font rendering: Ensure system has Greek font support (standard on Windows 11)
2. Right-to-left text: Greek is left-to-right, no special handling needed
3. PDF content: Only UI localization is provided; PDF processing is language-independent

## Future Enhancements

Potential improvements:
- Add more languages (Spanish, French, German, etc.)
- Implement RTL support for Arabic/Hebrew
- Create translation file format (JSON/YAML) for easier management
- Add language auto-detection based on system locale
- Implement in-app language switching without restart

## Support

For issues with Greek language support:

1. Verify system locale is set to Greek or UTF-8 compatible
2. Ensure font support with `chcp 65001` in Windows terminal
3. Check that `src/localization.py` exists and is in Python path
4. Run test suite: `python test_greek_localization.py`
5. Check audit logs for encoding errors

## Summary

The PDF Sanitizer now provides comprehensive Greek language support with:
- ✅ Full UI translation (35+ strings)
- ✅ Audit log support with UTF-8 encoding
- ✅ Language persistence through configuration
- ✅ Easy language switching from Settings
- ✅ Complete test coverage (9 tests)
- ✅ Framework for adding additional languages

Users can confidently use the application in Greek for secure PDF sanitization with full audit trail support in their native language.
