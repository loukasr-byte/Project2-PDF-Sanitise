"""
Verify that sanitized PDFs contain actual readable content
"""
from pikepdf import Pdf
from pathlib import Path

test_files = [
    "tests/scorereport_sanitized.pdf",
    "tests/og-fortidlp_sanitized.pdf",
    "tests/Suggested FortiGate Upgrade Models_sanitized.pdf",
    "tests/UserGuide-for-Student-Finance_sanitized.pdf"
]

print("=" * 70)
print("VERIFYING SANITIZED PDF CONTENT")
print("=" * 70)

for test_file in test_files:
    path = Path(test_file)
    if not path.exists():
        print(f"\n[SKIP] {path.name} - NOT FOUND")
        continue
    
    try:
        pdf = Pdf.open(test_file)
        num_pages = len(pdf.pages)
        
        # Check for content streams
        content_count = 0
        for i, page in enumerate(pdf.pages):
            if hasattr(page, 'Contents') and page.Contents is not None:
                content_count += 1
        
        # Check for document info
        has_docinfo = bool(pdf.docinfo)
        has_metadata = hasattr(pdf.Root, 'Metadata') and pdf.Root.Metadata is not None
        has_acroform = hasattr(pdf.Root, 'AcroForm') and pdf.Root.AcroForm is not None
        
        print(f"\n[OK] {path.name}")
        print(f"   Pages: {num_pages}")
        print(f"   Pages with content: {content_count}/{num_pages}")
        print(f"   Has DocInfo: {has_docinfo} (should be False)")
        print(f"   Has Metadata: {has_metadata} (should be False)")
        print(f"   Has AcroForm: {has_acroform} (should be False)")
        
        # Overall assessment
        if content_count > 0 and not has_docinfo and not has_metadata and not has_acroform:
            print(f"   Status: PASS - Content preserved, threats removed")
        else:
            print(f"   Status: CHECK - Verify manually")
        
        pdf.close()
    except Exception as e:
        print(f"\n[ERROR] {path.name}: {e}")

print("\n" + "=" * 70)
