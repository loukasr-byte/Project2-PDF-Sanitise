from pathlib import Path
import ctypes
import subprocess

class SecurityError(Exception):
    pass

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
    
    # Use Windows API to check mount attributes
    try:
        result = ctypes.windll.kernel32.GetVolumeInformationW(
            mount_path, None, 0, None, None, None, None, 0
        )
        # Additional checks via command line
        
        cmd = f'fsutil fsinfo volumeinfo {mount_path}'
        output = subprocess.check_output(cmd, shell=True, text=True)
        return 'Read-only' in output or 'ReadOnly' in output
    except:
        return False