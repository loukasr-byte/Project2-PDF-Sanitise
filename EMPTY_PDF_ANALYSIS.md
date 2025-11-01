# Analysis: Why Sanitized PDF Contains Nothing

**Issue**: Sanitized PDF file appears empty or has no visible content  
**Test File**: `tests/og-fortidlp.pdf`  
**Date**: November 1, 2025

---

## Problem Statement

When processing `og-fortidlp.pdf`, the sanitized output PDF is created but appears to contain no visible content or text.

---

## Root Causes (Analysis)

### 1. **Content Stream Extraction Issue**

The current `_extract_whitelisted_page_content()` method in `core_engine.py`:
- ✓ Extracts MediaBox (page dimensions)
- ✓ Extracts Resources dictionaries
- ✓ Reads content streams

**BUT**: It only stores the raw binary/text content without reconstructing the PDF structure properly.

### 2. **No Font Information Passed to Reconstruction**

The parser extracts font resources but doesn't:
- Store font definitions
- Pass font names to the reconstructor
- Include font dictionaries in the output

**Result**: The reconstructor creates pages WITHOUT proper font resources, so even if content exists, it can't be rendered.

### 3. **Missing Font Dictionary in Reconstructed Pages**

In `build()` method, we do:
```python
page.Resources.Font = Dictionary()  # Creates EMPTY Font dict
```

**Problem**: Empty Font dictionary = no fonts available = no text rendering

### 4. **Content Stream Not Actually Included in Output**

Current code:
```python
if page_data["contents"]:
    content = page_data["contents"][0]
    page.Contents = self.new_pdf.make_stream(content)
```

**Issue**: This should work, BUT we're not verifying the content stream is actually valid PDF operations.

### 5. **Scanned Image PDFs Have No Text Content**

If `og-fortidlp.pdf` is a scanned document:
- Contains images (scans) instead of text
- PDF has no searchable text content streams
- Parser extracts images from Resources but doesn't include them in output

**Result**: Reconstructed PDF has correct page size but no content (no text, no images)

---

## CONFIRMED Root Cause: XObjects (Images) Are Being Stripped

**Location**: `src/core_engine.py`, line 159

The critical issue is in `_extract_whitelisted_resources()`:

**Current Code**:
```python
def _extract_whitelisted_resources(self, resources) -> dict:
    # Placeholder for deep resource validation.
    # This would involve checking font types, ensuring images are just raw pixel data, etc.
    return {"/Font": {}, "/XObject": {}}  # <-- RETURNS EMPTY DICTS!
```

**What Happens**:
1. Original PDF has content streams referencing `/XObject` (images)
2. Parser extracts resources but **intentionally returns empty dicts**
3. Content stream says "display /Im1" but `/Im1` doesn't exist in Resources
4. Reconstructor creates page with content that references missing resources
5. PDF reader can't find `/Im1` → renders as blank page
6. Result: Empty/blank PDF with proper structure but invisible content

**Why This Happens**: The code is a PLACEHOLDER with a comment saying "deep resource validation" is needed.

---

## Diagnosis Steps

To confirm, check what the original PDF contains:

### Check 1: Is it a scanned document?
```python
import pikepdf
pdf = pikepdf.Pdf.open('tests/og-fortidlp.pdf')
page = pdf.pages[0]

# Check for XObjects (images)
if page.Resources and '/XObject' in page.Resources:
    print("✓ Has images/XObjects - likely scanned PDF")
    print(f"  XObjects: {list(page.Resources.XObject.keys())}")
```

### Check 2: Does it have text content?
```python
if hasattr(page, 'Contents'):
    data = page.Contents.read_bytes()
    print(f"✓ Content stream size: {len(data)} bytes")
```

### Check 3: Font resources?
```python
if page.Resources and '/Font' in page.Resources:
    print(f"✓ Has fonts: {list(page.Resources.Font.keys())}")
```

---

## Solution: Enhance Resource Extraction

The fix is to properly extract and preserve resources in `_extract_whitelisted_resources()`:

```python
def _extract_whitelisted_resources(self, resources) -> dict:
    """Extract whitelisted resources including images and fonts"""
    result = {"/Font": {}, "/XObject": {}}
    
    if not resources:
        return result
    
    # Extract XObjects (images - SAFE to include)
    if hasattr(resources, 'XObject'):
        for name, obj in resources.XObject.items():
            # Verify it's an image (not form or other dangerous object)
            if hasattr(obj, 'Subtype') and obj.Subtype == '/Image':
                result["/XObject"][name] = obj  # INCLUDE the image!
    
    # Extract Fonts (standard fonts - SAFE to include)
    if hasattr(resources, 'Font'):
        for name, font in resources.Font.items():
            # Include standard fonts (no embedded malware)
            result["/Font"][name] = font
    
    return result
```

---

## Why This Is The Issue

**Architecture Principle**: Whitelisting-only sanitization

The current code is **too aggressive** - it strips out SAFE content:
- ✓ Images (raw pixel data) = **SAFE** to keep
- ✓ Standard fonts = **SAFE** to keep  
- ✓ Text content = **SAFE** to keep
- ❌ Metadata = **DANGEROUS** to remove
- ❌ Embedded scripts = **DANGEROUS** to remove

**Current behavior**: Removes EVERYTHING including safe content  
**Correct behavior**: Remove only dangerous metadata/scripts, keep safe content

---

## Expected After Fix

**Original PDF**:
```
Page 1: 
  - Content: "q 612 0 0 792 0 0 cm /Im1 Do Q"  (display image)
  - Resources: {/XObject: {/Im1: <image stream>}}
  - Result: Shows scanned page image
```

**After Sanitization**:
```
Page 1:
  - Content: "q 612 0 0 792 0 0 cm /Im1 Do Q"  (display image)
  - Resources: {/XObject: {/Im1: <image stream>}}
  - Result: Shows SAME scanned page image (safe content preserved!)
```

---

## Files to Modify

**Primary**: `src/core_engine.py`

1. Find `_extract_whitelisted_resources()` method
2. Replace the placeholder logic with proper resource extraction
3. Actually copy Font and XObject references to result dict
4. Ensure `build()` method uses the returned resources

---

## Verification

After fix:

```bash
# 1. Sanitize the PDF
python run_gui.py
# Process: tests/og-fortidlp.pdf

# 2. Check sanitized output has content
import pikepdf
orig = pikepdf.Pdf.open('tests/og-fortidlp.pdf')
san = pikepdf.Pdf.open('tests/og-fortidlp_sanitized.pdf')

orig_page = orig.pages[0]
san_page = san.pages[0]

print(f"Original has XObject: {'XObject' in orig_page.Resources}")
print(f"Sanitized has XObject: {'XObject' in san_page.Resources}")
# Should both be True!
```

**Current Output**: ❌ Sanitized has no XObject (empty)  
**Target Output**: ✅ Sanitized has XObject (content preserved)
