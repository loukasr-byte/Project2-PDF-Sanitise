import unittest
import os
from pathlib import Path
import time
from src.sandboxing import SandboxedPDFParser

class TestSandboxing(unittest.TestCase):
    def setUp(self):
        # Create a dummy worker script for testing
        dummy_worker_content = """
import json
import time
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--whitelist-mode", default="strict")
    args = parser.parse_args()
    
    time.sleep(2) # Simulate work
    
    output_path = Path(args.output)
    result = {
        "status": "success",
        "input_file": args.input,
        "extracted_objects": 10,
        "threats_found": 0
    }
    (output_path / "result.json").write_text(json.dumps(result))

if __name__ == "__main__":
    main()
"""
        with open("worker_pdf_parser.py", "w") as f:
            f.write(dummy_worker_content)
            
        # Create a dummy PDF for testing
        with open("test.pdf", "w") as f:
            f.write("%PDF-1.7\n%DUMMY")

        self.parser = SandboxedPDFParser("worker_pdf_parser.py")

    def test_parse_pdf_isolated(self):
        # Test if the sandboxed parser can successfully parse a PDF
        result = self.parser.parse_pdf_isolated("test.pdf")
        self.assertEqual(result["status"], "success")

    def tearDown(self):
        # Clean up the dummy files
        os.remove("worker_pdf_parser.py")
        os.remove("test.pdf")

if __name__ == '__main__':
    unittest.main()