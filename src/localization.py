"""
Module: localization
Description: Provides multilingual support for the PDF Sanitizer application.
Currently supports English and Greek languages.
"""

# Language codes
ENGLISH = 'en'
GREEK = 'el'

# Supported languages
SUPPORTED_LANGUAGES = {
    ENGLISH: 'English',
    GREEK: 'Ελληνικά'
}

class Localization:
    """
    Centralized localization manager for all application strings.
    Supports English and Greek.
    """
    
    # All translatable strings organized by module/context
    TRANSLATIONS = {
        'main_window_title': {
            ENGLISH: 'Government-Grade PDF Sanitizer - Phase 1 (Windows 11)',
            GREEK: 'Κρατικής Κατηγορίας Αποστείρωση PDF - Φάση 1 (Windows 11)'
        },
        'menu_file': {
            ENGLISH: '&File',
            GREEK: '&Αρχείο'
        },
        'menu_open_pdf': {
            ENGLISH: '&Open PDF...',
            GREEK: '&Άνοιγμα PDF...'
        },
        'menu_exit': {
            ENGLISH: 'E&xit',
            GREEK: '&Έξοδος'
        },
        'menu_help': {
            ENGLISH: '&Help',
            GREEK: '&Βοήθεια'
        },
        'menu_about': {
            ENGLISH: '&About',
            GREEK: '&Σχετικά με'
        },
        'tab_sanitize': {
            ENGLISH: 'Sanitize',
            GREEK: 'Αποστείρωση'
        },
        'tab_history': {
            ENGLISH: 'History',
            GREEK: 'Ιστορικό'
        },
        'tab_settings': {
            ENGLISH: 'Settings',
            GREEK: 'Ρυθμίσεις'
        },
        'tab_reports': {
            ENGLISH: 'Reports',
            GREEK: 'Αναφορές'
        },
        'sanitize_instructions': {
            ENGLISH: 'Select PDF files to sanitize. PDFs are processed in an isolated subprocess with strict resource limits and whitelist-only threat model.',
            GREEK: 'Επιλέξτε αρχεία PDF για αποστείρωση. Τα PDF επεξεργάζονται σε απομονωμένη διαδικασία με αυστηρά όρια ресурсов και μοντέλο απειλών μόνο λευκής λίστας.'
        },
        'files_in_queue': {
            ENGLISH: 'Files in Queue:',
            GREEK: 'Αρχεία σε Ουρά:'
        },
        'btn_open_pdf': {
            ENGLISH: 'Open PDF',
            GREEK: 'Άνοιγμα PDF'
        },
        'btn_process_queue': {
            ENGLISH: 'Process Queue',
            GREEK: 'Επεξεργασία Ουράς'
        },
        'btn_clear_queue': {
            ENGLISH: 'Clear Queue',
            GREEK: 'Εκκαθάριση Ουράς'
        },
        'dialog_open_pdf': {
            ENGLISH: 'Open PDF File',
            GREEK: 'Άνοιγμα Αρχείου PDF'
        },
        'dialog_pdf_filter': {
            ENGLISH: 'PDF Files (*.pdf);;All Files (*)',
            GREEK: 'Αρχεία PDF (*.pdf);;Όλα τα αρχεία (*)'
        },
        'status_ready': {
            ENGLISH: 'Ready - USB Isolation Monitoring Active',
            GREEK: 'Έτοιμο - Παρακολούθηση Απομόνωσης USB Ενεργή'
        },
        'status_added_to_queue': {
            ENGLISH: 'Added to queue: {}',
            GREEK: 'Προστέθηκε στην ουρά: {}'
        },
        'status_sanitizing': {
            ENGLISH: 'Sanitizing: {}...',
            GREEK: 'Αποστείρωση: {}...'
        },
        'status_success': {
            ENGLISH: '✓ Successfully sanitized: {}',
            GREEK: '✓ Επιτυχώς αποστειρωθεί: {}'
        },
        'status_failed': {
            ENGLISH: '✗ Failed to sanitize: {}',
            GREEK: '✗ Αποτυχία αποστείρωσης: {}'
        },
        'status_queue_empty': {
            ENGLISH: 'Queue is empty',
            GREEK: 'Η ουρά είναι κενή'
        },
        'status_queue_cleared': {
            ENGLISH: 'Queue cleared',
            GREEK: 'Ουρά εκκαθαρίστηκε'
        },
        'dialog_success_title': {
            ENGLISH: 'Sanitization Success',
            GREEK: 'Επιτυχία Αποστείρωσης'
        },
        'dialog_success_message': {
            ENGLISH: 'PDF successfully sanitized!\n\nOriginal: {}\nSanitized: {}\n\nCheck the Reports tab for details.',
            GREEK: 'Το PDF αποστειρώθηκε με επιτυχία!\n\nΑρχικό: {}\nΑποστειρωμένο: {}\n\nΕλέγξτε την καρτέλα Αναφορές για λεπτομέρειες.'
        },
        'dialog_error_title': {
            ENGLISH: 'Sanitization Error',
            GREEK: 'Σφάλμα Αποστείρωσης'
        },
        'dialog_error_message': {
            ENGLISH: 'Failed to sanitize PDF:\n\nFile: {}\n\nError: {}\n\nTROUBLESHOOTING:\n1. Check file exists and is readable\n2. Ensure sufficient disk space\n3. Try saving output to a different location (e.g., Desktop)\n4. Check audit logs in \'logs\' folder for details',
            GREEK: 'Αποτυχία αποστείρωσης PDF:\n\nΑρχείο: {}\n\nΣφάλμα: {}\n\nΠΡΟΒΛΗΜΑΤΑ:\n1. Ελέγξτε ότι το αρχείο υπάρχει και είναι αναγνώσιμο\n2. Βεβαιωθείτε ότι υπάρχει επαρκής χώρος δίσκου\n3. Δοκιμάστε να αποθηκεύσετε το αποτέλεσμα σε διαφορετική θέση (π.χ., Επιφάνεια εργασίας)\n4. Ελέγξτε τα αρχεία ελέγχου στο φάκελο \'logs\' για λεπτομέρειες'
        },
        'dialog_clear_queue_title': {
            ENGLISH: 'Clear Queue',
            GREEK: 'Εκκαθάριση Ουράς'
        },
        'dialog_clear_queue_message': {
            ENGLISH: 'Clear all {} file(s) from the queue?',
            GREEK: 'Εκκαθάρετε όλα τα {} αρχείο(α) από την ουρά;'
        },
        'settings_policy_label': {
            ENGLISH: 'Sanitization Policy:',
            GREEK: 'Πολιτική Αποστείρωσης:'
        },
        'settings_policy_aggressive': {
            ENGLISH: 'AGGRESSIVE',
            GREEK: 'ΕΠΙΘΕΤΙΚΗ'
        },
        'settings_memory_label': {
            ENGLISH: 'Memory Limit:',
            GREEK: 'Όριο Μνήμης:'
        },
        'settings_memory_suffix': {
            ENGLISH: ' MB',
            GREEK: ' MB'
        },
        'settings_timeout_label': {
            ENGLISH: 'Timeout:',
            GREEK: 'Χρονικό όριο:'
        },
        'settings_timeout_suffix': {
            ENGLISH: ' seconds',
            GREEK: ' δευτερόλεπτα'
        },
        'settings_usb_label': {
            ENGLISH: 'Enable USB Isolation Monitoring:',
            GREEK: 'Ενεργοποίηση Παρακολούθησης Απομόνωσης USB:'
        },
        'settings_audit_label': {
            ENGLISH: 'Enable Audit Logging:',
            GREEK: 'Ενεργοποίηση Καταγραφής Ελέγχου:'
        },
        'settings_language_label': {
            ENGLISH: 'Language:',
            GREEK: 'Γλώσσα:'
        },
        'settings_info': {
            ENGLISH: 'Note: Advanced configuration requires administrator privileges.\nThese settings control PDF processing constraints and security features.',
            GREEK: 'Σημείωση: Η ανώτερη διαμόρφωση απαιτεί δικαιώματα διαχειριστή.\nΑυτές οι ρυθμίσεις ελέγχουν τους περιορισμούς επεξεργασίας PDF και τις δυνατότητες ασφαλείας.'
        },
        'about_title': {
            ENGLISH: 'About Government-Grade PDF Sanitizer',
            GREEK: 'Σχετικά με την Κρατικής Κατηγορίας Αποστείρωση PDF'
        },
        'about_message': {
            ENGLISH: 'Version 1.0 (Phase 1)\n\nA defense-grade PDF sanitizer for classified document handling.\nWhitelisting-only threat model with sandboxed processing.\n\n© 2025 Kilo Code',
            GREEK: 'Έκδοση 1.0 (Φάση 1)\n\nΑποστειρωτής PDF άμυνας για χειρισμό ταξινομημένων εγγράφων.\nΜοντέλο απειλών μόνο λευκής λίστας με απομονωμένη επεξεργασία.\n\n© 2025 Kilo Code'
        },
        'processing_error_title': {
            ENGLISH: 'Processing Error',
            GREEK: 'Σφάλμα Επεξεργασίας'
        },
        'processing_error_message': {
            ENGLISH: 'Failed to process queue:\n{}',
            GREEK: 'Αποτυχία επεξεργασίας ουράς:\n{}'
        },
        'audit_log_pdf_opened': {
            ENGLISH: 'PDF file opened',
            GREEK: 'Το αρχείο PDF ανοίχθηκε'
        },
        'audit_log_pdf_sanitized': {
            ENGLISH: 'PDF file sanitized',
            GREEK: 'Το αρχείο PDF αποστειρώθηκε'
        },
        'audit_log_sanitization_failed': {
            ENGLISH: 'Sanitization failed',
            GREEK: 'Η αποστείρωση απέτυχε'
        },
        'audit_log_parsing_in_progress': {
            ENGLISH: 'Parsing in progress',
            GREEK: 'Ανάλυση σε εξέλιξη'
        },
        'audit_log_reconstruction_in_progress': {
            ENGLISH: 'Reconstruction in progress',
            GREEK: 'Ανακατασκευή σε εξέλιξη'
        },
    }
    
    def __init__(self, language=ENGLISH):
        """Initialize with specified language (default: English)"""
        self.language = language if language in SUPPORTED_LANGUAGES else ENGLISH
    
    def set_language(self, language_code):
        """Set the current language"""
        if language_code in SUPPORTED_LANGUAGES:
            self.language = language_code
        else:
            self.language = ENGLISH
    
    def get_language(self):
        """Get the current language code"""
        return self.language
    
    def get_language_name(self, language_code=None):
        """Get the display name for a language"""
        lang = language_code or self.language
        return SUPPORTED_LANGUAGES.get(lang, 'Unknown')
    
    def t(self, key, *args, **kwargs):
        """
        Translate a key to the current language.
        Supports string formatting with positional or keyword arguments.
        
        Example:
            localization.t('status_added_to_queue', 'file.pdf')
            localization.t('dialog_clear_queue_message', 5)
        """
        if key not in self.TRANSLATIONS:
            return key  # Return key if translation not found
        
        text = self.TRANSLATIONS[key].get(self.language, self.TRANSLATIONS[key].get(ENGLISH, key))
        
        # Format with positional arguments
        if args:
            try:
                return text.format(*args)
            except (IndexError, KeyError):
                return text
        
        # Format with keyword arguments
        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError:
                return text
        
        return text
    
    def get_all_keys(self):
        """Get all available translation keys"""
        return list(self.TRANSLATIONS.keys())


# Global localization instance
_localization_instance = None

def get_localization(language=ENGLISH):
    """Get or create the global localization instance"""
    global _localization_instance
    if _localization_instance is None:
        _localization_instance = Localization(language)
    return _localization_instance

def set_language(language_code):
    """Set the language globally"""
    loc = get_localization()
    loc.set_language(language_code)

def t(key, *args, **kwargs):
    """Translate a key using the global localization instance"""
    loc = get_localization()
    return loc.t(key, *args, **kwargs)
