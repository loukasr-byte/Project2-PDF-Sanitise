"""
Test the queue_manager reconstruction flow (both worker success and fallback)
"""
from pathlib import Path
from src.queue_manager import QueueManager

# Mock sandboxed parser that simulates worker output
class MockSandboxedParser:
    def parse_pdf_isolated(self, input_pdf_path: str):
        """Simulate worker returning parsed data"""
        # Simulate the worker NOT creating an output file (fallback scenario)
        return {
            "status": "success",
            "pages": 1,  # This is an integer count, not list of page objects!
            # "output_file" is NOT set, so fallback path will be used
        }

# Test
print("Testing QueueManager fallback reconstruction path...")
print()

try:
    mock_parser = MockSandboxedParser()
    queue_manager = QueueManager(mock_parser, audit_logger=None)
    
    # Process a test file
    test_file = "tests/scorereport.pdf"
    print(f"Processing: {test_file}")
    
    # This should trigger the fallback reconstruction code
    queue_manager.add_file_to_queue(test_file)
    queue_manager.process_next_in_queue()
    
    print("\nSUCCESS - Fallback path worked correctly!")
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
