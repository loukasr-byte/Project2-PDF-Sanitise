# -*- coding: utf-8 -*-
"""
Test script to verify Greek language support in the PDF Sanitizer.
This tests the localization module and verifies Greek translations are available.
"""

import sys
from pathlib import Path

# Add parent directory to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.localization import (
    Localization, get_localization, set_language, t,
    ENGLISH, GREEK, SUPPORTED_LANGUAGES
)

def test_supported_languages():
    """Test that English and Greek are supported."""
    print("Testing supported languages... ", end="", flush=True)
    assert ENGLISH in SUPPORTED_LANGUAGES
    assert GREEK in SUPPORTED_LANGUAGES
    assert SUPPORTED_LANGUAGES[ENGLISH] == 'English'
    # Greek display name should be non-empty (actual string may be in Greek)
    assert len(SUPPORTED_LANGUAGES[GREEK]) > 0
    print("[PASS]")

def test_english_localization():
    """Test English localization."""
    print("Testing English localization... ", end="", flush=True)
    loc = Localization(ENGLISH)
    
    tests = [
        ('main_window_title', 'Government-Grade PDF Sanitizer'),
        ('menu_file', '&File'),
        ('btn_open_pdf', 'Open PDF'),
        ('tab_sanitize', 'Sanitize'),
    ]
    
    for key, expected_substring in tests:
        result = loc.t(key)
        assert expected_substring in result, f"Expected '{expected_substring}' in '{result}'"
    print("[PASS]")

def test_greek_localization():
    """Test Greek localization."""
    print("Testing Greek localization... ", end="", flush=True)
    loc = Localization(GREEK)
    
    # Test that Greek translations return non-empty strings
    tests = [
        'main_window_title',
        'menu_file',
        'btn_open_pdf',
        'tab_sanitize',
        'dialog_success_title',
        'dialog_error_title',
    ]
    
    for key in tests:
        result = loc.t(key)
        assert len(result) > 0, f"Greek translation for {key} is empty"
        # Verify it's different from English
        english_result = Localization(ENGLISH).t(key)
        assert result != english_result, f"Greek and English translations are identical for {key}"
    print("[PASS]")

def test_greek_dialogs():
    """Test Greek translation of dialog messages."""
    print("Testing Greek dialog messages... ", end="", flush=True)
    loc = Localization(GREEK)
    
    success_msg = loc.t('dialog_success_message', '/path/to/original.pdf', '/path/to/sanitized.pdf')
    assert len(success_msg) > 0
    assert 'original.pdf' in success_msg
    assert 'sanitized.pdf' in success_msg
    
    error_msg = loc.t('dialog_error_message', '/path/to/file.pdf', 'Test error')
    assert len(error_msg) > 0
    assert 'file.pdf' in error_msg
    print("[PASS]")

def test_language_switching():
    """Test dynamic language switching."""
    print("Testing language switching... ", end="", flush=True)
    loc = Localization(ENGLISH)
    
    english_title = loc.t('main_window_title')
    assert 'Government' in english_title
    
    loc.set_language(GREEK)
    greek_title = loc.t('main_window_title')
    
    assert english_title != greek_title
    assert 'Government' not in greek_title  # Should not have English text
    print("[PASS]")

def test_global_localization():
    """Test global localization functions."""
    print("Testing global localization functions... ", end="", flush=True)
    
    # Test global instance
    loc = get_localization(GREEK)
    result = loc.t('tab_sanitize')
    assert len(result) > 0
    
    # Test global t function
    result_t = t('btn_clear_queue')
    assert len(result_t) > 0
    print("[PASS]")

def test_string_formatting():
    """Test string formatting with translations."""
    print("Testing string formatting... ", end="", flush=True)
    loc = Localization(GREEK)
    
    # Test with single argument
    msg = loc.t('status_added_to_queue', 'test_file.pdf')
    assert 'test_file.pdf' in msg
    
    # Test with multiple arguments
    msg = loc.t('dialog_success_message', 'file1.pdf', 'file2.pdf')
    assert 'file1.pdf' in msg and 'file2.pdf' in msg
    print("[PASS]")

def test_greek_audit_translations():
    """Test Greek translations for audit log messages."""
    print("Testing Greek audit translations... ", end="", flush=True)
    loc = Localization(GREEK)
    
    audit_keys = [
        'audit_log_pdf_opened',
        'audit_log_pdf_sanitized',
        'audit_log_sanitization_failed',
        'audit_log_parsing_in_progress',
        'audit_log_reconstruction_in_progress',
    ]
    
    for key in audit_keys:
        result = loc.t(key)
        assert len(result) > 0
    print("[PASS]")

def test_all_keys_coverage():
    """Test that all translation keys have both English and Greek translations."""
    print("Testing translation key coverage... ", end="", flush=True)
    loc_en = Localization(ENGLISH)
    loc_gr = Localization(GREEK)
    
    keys = loc_en.get_all_keys()
    assert len(keys) >= 35, f"Should have at least 35 translation keys, got {len(keys)}"
    
    # Keys that don't need translation (units, symbols, etc.)
    no_translation_keys = {'settings_memory_suffix', 'settings_timeout_suffix', 'dialog_pdf_filter'}
    
    for key in keys:
        en_text = loc_en.t(key)
        gr_text = loc_gr.t(key)
        
        # Both should have content
        assert len(en_text) > 0, f"English translation for {key} is empty"
        assert len(gr_text) > 0, f"Greek translation for {key} is empty"
        
        # They should be different (except for keys that don't need translation)
        if key not in no_translation_keys:
            assert en_text != gr_text, f"English and Greek are the same for {key}"
    print("[PASS]")

def main():
    """Run all tests."""
    print("=" * 70)
    print("Greek Language Support Test Suite")
    print("=" * 70)
    print()
    
    tests = [
        ('Supported Languages', test_supported_languages),
        ('English Localization', test_english_localization),
        ('Greek Localization', test_greek_localization),
        ('Greek Dialogs', test_greek_dialogs),
        ('Language Switching', test_language_switching),
        ('Global Localization', test_global_localization),
        ('String Formatting', test_string_formatting),
        ('Audit Translations', test_greek_audit_translations),
        ('Key Coverage', test_all_keys_coverage),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] - {str(e)}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] - {str(e)}")
            failed += 1
    
    print()
    print("=" * 70)
    print(f"Test Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("[SUCCESS] All tests passed! Greek language support is functional.")
    else:
        print("[FAILURE] Some tests failed.")
    print("=" * 70)
    
    return 0 if failed == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
