import json
import sys
import os
import logging
import traceback
from pathlib import Path
from decimal import Decimal

# Setup logging to stderr so it appears in subprocess output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal objects and other non-serializable objects from pikepdf"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        # Handle other non-serializable objects by converting to string
        # This prevents "Object is not JSON serializable" errors
        try:
            return str(obj)
        except Exception:
            return repr(obj)

def main():
    """
    This is the entry point for the sandboxed PDF parsing process.
    It will parse the PDF and directly reconstruct a sanitized version.
    """
    logger.info("Worker process started.")
    
    # Add the parent directory to sys.path so we can import src module
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"sys.path: {sys.path[:3]}")
    
    input_file = ""
    output_dir = ""
    output_pdf = ""
    for i, arg in enumerate(sys.argv):
        if arg == "--input" and i + 1 < len(sys.argv):
            input_file = sys.argv[i+1]
        elif arg == "--output" and i + 1 < len(sys.argv):
            output_dir = sys.argv[i+1]

    logger.info(f"Input file: {input_file}")
    logger.info(f"Output dir: {output_dir}")

    if not input_file or not output_dir:
        logger.error("Usage: python worker_pdf_parser.py --input <path> --output <path>")
        sys.exit(1)

    # Generate output PDF path (sanitized)
    input_path = Path(input_file)
    output_pdf = os.path.join(output_dir, f"{input_path.stem}_sanitized.pdf")

    try:
        logger.info("Importing PDF modules...")
        from src.core_engine import PDFWhitelistParser, PDFReconstructor
        
        logger.info(f"Parsing PDF: {input_file}")
        parser = PDFWhitelistParser(input_file)
        whitelisted_data = parser.parse()
        logger.info(f"Extracted metadata from {len(whitelisted_data.get('pages', []))} pages")
        
        # Get the original PDF for content extraction
        original_pdf = parser.get_original_pdf()
        
        logger.info(f"Reconstructing sanitized PDF...")
        reconstructor = PDFReconstructor(whitelisted_data, original_pdf)
        reconstructor.build(output_pdf)
        
        logger.info(f"Sanitized PDF saved to: {output_pdf}")
        
        # Write status result
        result_data = {
            "status": "success",
            "output_file": output_pdf,
            "pages": len(whitelisted_data.get('pages', []))
        }
        output_file = os.path.join(output_dir, "result.json")
        logger.info(f"Writing result to: {output_file}")
        with open(output_file, "w") as f:
            json.dump(result_data, f, indent=2, cls=DecimalEncoder)
        logger.info("Sanitization complete, worker exiting successfully")
        
    except Exception as e:
        logger.error(f"Error during sanitization: {e}")
        logger.error(traceback.format_exc())
        result_data = {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }
        output_file = os.path.join(output_dir, "result.json")
        try:
            with open(output_file, "w") as f:
                json.dump(result_data, f, indent=2, cls=DecimalEncoder)
        except Exception as write_err:
            logger.error(f"Failed to write error result: {write_err}")
        sys.exit(1)

if __name__ == "__main__":
    main()
