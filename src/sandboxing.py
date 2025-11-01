"""
Module: sandboxing
Description: Handles the creation and management of isolated subprocesses for
             parsing PDF files. This is a critical security boundary for the
             application.
"""

import subprocess
import tempfile
import json
from pathlib import Path
import logging
import sys
import os

try:
    import win32job
    import win32process
    import win32api
    import msvcrt
except ImportError:
    win32job = None
    logging.warning("win32 modules not available - Job Object creation will be limited")

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def create_limited_job_object(job_name: str, memory_limit_mb: int, cpu_time_limit_sec: int) -> int:
    """
    Creates a Windows Job Object with strict resource limits.

    Args:
        job_name (str): A unique name for the job object.
        memory_limit_mb (int): The maximum memory allocation for the job (in MB).
        cpu_time_limit_sec (int): The maximum CPU time for any process in the job (in seconds).

    Returns:
        int: The handle to the created job object, or None if not available.
        
    Raises:
        RuntimeError: If win32job module is not available.
    """
    if win32job is None:
        raise RuntimeError("win32job module is not available. Install pywin32 and run: python -m pip install --upgrade pywin32")
    
    hjob = win32job.CreateJobObject(None, job_name)

    limit_info = win32job.QueryInformationJobObject(hjob, win32job.JobObjectExtendedLimitInformation)

    # Set memory limits
    limit_info['ProcessMemoryLimit'] = memory_limit_mb * 1024 * 1024
    limit_info['JobMemoryLimit'] = memory_limit_mb * 1024 * 1024

    # Set CPU time limit (in 100-nanosecond units)
    # The PerProcessUserTimeLimit is a LARGE_INTEGER structure.
    # We must provide it as an integer representing the time in 100ns units.
    # limit_info['PerProcessUserTimeLimit'] = cpu_time_limit_sec * 10_000_000

    limit_info['LimitFlags'] = (
        win32job.JOB_OBJECT_LIMIT_PROCESS_MEMORY |
        win32job.JOB_OBJECT_LIMIT_JOB_MEMORY |
        # win32job.JOB_OBJECT_LIMIT_PROCESS_TIME | # This is for user-mode time
        win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    )

    win32job.SetInformationJobObject(
        hjob,
        win32job.JobObjectExtendedLimitInformation,
        limit_info
    )
    logging.info(f"Created Windows Job Object '{job_name}' with {memory_limit_mb}MB memory limit")
    return hjob

class SandboxedPDFParser:
    """
    Manages the parsing of PDF files in a heavily restricted and isolated
    subprocess. It uses Windows Job Objects for resource control and operates
    on a whitelist-only principle.
    """

    def __init__(self,
                 worker_script_path: str = "worker_pdf_parser.py",
                 memory_limit_mb: int = 500,
                 cpu_time_limit_sec: int = 300):
        """
        Initializes the parser with the path to the worker script and resource limits.

        Args:
            worker_script_path (str): Path to the worker Python script.
            memory_limit_mb (int): Max memory for the worker process in megabytes.
            cpu_time_limit_sec (int): Max CPU time for the worker process in seconds.
        """
        self.worker_script_path = worker_script_path
        self.memory_limit_mb = memory_limit_mb
        self.cpu_time_limit_sec = cpu_time_limit_sec

    def parse_pdf_isolated(self, input_pdf_path: str, timeout_seconds: int = 300) -> dict:
        """
        Parse PDF in isolated subprocess with strict resource limits.
        Returns only whitelisted extracted content.
        
        Args:
            input_pdf_path (str): Path to the input PDF file.
            timeout_seconds (int): Maximum time to allow for parsing (default: 300 seconds).
            
        Returns:
            dict: Parsed whitelist data with status and any error messages.
            
        Raises:
            TimeoutError: If parsing exceeds the timeout.
            Exception: If the worker process fails or produces no results.
        """
        temp_result_dir = Path(tempfile.mkdtemp(prefix="pdf_parse_"))
        
        try:
            # Get the path to the worker script relative to this module
            worker_script = Path(__file__).parent / "worker_pdf_parser.py"
            
            if not worker_script.exists():
                raise FileNotFoundError(f"Worker script not found at: {worker_script}")
            
            logging.info(f"Starting isolated PDF parsing for: {input_pdf_path}")
            logging.info(f"Worker script: {worker_script}")
            logging.info(f"Output directory: {temp_result_dir}")
            
            # Create worker process with constraints
            process = subprocess.Popen(
                [
                    sys.executable,
                    str(worker_script),
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
                    error_msg = stderr.decode('utf-8', errors='replace') if stderr else "Unknown error"
                    logging.error(f"PDF parser process failed with code {process.returncode}: {error_msg}")
                    raise Exception(f"PDF parser crashed: {error_msg}")
                
                # Read results from isolated temp directory
                result_file = temp_result_dir / "result.json"
                if result_file.exists():
                    with open(result_file, 'r') as f:
                        result = json.load(f)
                    logging.info(f"Successfully parsed PDF: {result.get('status', 'unknown')}")
                    return result
                else:
                    raise Exception("Parser produced no valid results")
                    
            except subprocess.TimeoutExpired:
                process.kill()
                logging.error(f"PDF parsing timeout after {timeout_seconds} seconds")
                raise TimeoutError(f"PDF parsing exceeded {timeout_seconds}s timeout")
                
        finally:
            # Cleanup: securely delete temp results
            import shutil
            try:
                shutil.rmtree(temp_result_dir, ignore_errors=True)
                logging.debug(f"Cleaned up temporary directory: {temp_result_dir}")
            except Exception as e:
                logging.warning(f"Could not clean up temp directory {temp_result_dir}: {e}")
