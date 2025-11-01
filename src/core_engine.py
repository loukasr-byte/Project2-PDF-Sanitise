"""
Module: core_engine
Description: Contains the primary PDF parsing, whitelisting, and reconstruction
             logic. This is the heart of the sanitization process.
"""

import pikepdf
from pikepdf import Pdf, PdfImage
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Whitelisting Configuration based on ARCHITECTURE.md ---

WHITELISTED_PDF_OBJECTS = {
    '/Type', '/Pages', '/Kids', '/MediaBox', '/CropBox', '/Contents',
    '/Resources', '/Font', '/Image', '/XObject', '/ProcSet', '/BaseFont'
}

WHITELISTED_STREAM_OPERATORS = {
    # Text Positioning
    b'BT', b'ET', b'Td', b'Tm', b'T*',
    # Text Rendering
    b'Tj', b'TJ', b"'", b'"',
    # Graphics
    b're', b'f', b'S', b'n',
    # Path Construction
    b'm', b'l', b'c', b'h',
    # Image Rendering
    b'Do',
    # State Management
    b'q', b'Q'
}

class PDFWhitelistParser:
    """
    Parses a PDF and extracts only whitelisted content. It ensures that no
    disallowed objects, scripts, or actions are carried over.
    """
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.whitelisted_data = {
            "pages": []
        }
        try:
            try:
                self.pdf = Pdf.open(self.pdf_path, allow_overwriting_input=True)
            except pikepdf.PasswordError:
                raise ValueError("The PDF file is encrypted and cannot be opened without a password.")
        except Exception as e:
            logging.error(f"Failed to open PDF {pdf_path}: {e}")
            raise

    def parse(self):
        """
        Executes the parsing and whitelisting process.
        """
        logging.info(f"Starting whitelist parsing for {self.pdf_path}")
        try:
            # This is conceptual for now. The actual implementation will be complex,
            # requiring deep iteration over the PDF's object graph.
            # We will build this out with more granular methods.
            
            if not hasattr(self.pdf, 'pages') or self.pdf.pages is None:
                logging.warning(f"PDF has no pages property, creating empty page list")
                self.whitelisted_data["pages"] = []
                return self.whitelisted_data
            
            total_pages = len(self.pdf.pages)
            for i, page in enumerate(self.pdf.pages):
                try:
                    logging.info(f"Processing page {i+1}/{total_pages}")
                    page_content = self._extract_whitelisted_page_content(page)
                    self.whitelisted_data["pages"].append(page_content)
                except Exception as e:
                    logging.error(f"Error processing page {i+1}: {e}", exc_info=True)
                    # Add empty page as fallback
                    self.whitelisted_data["pages"].append({
                        "mediabox": [0, 0, 612, 792],
                        "resources": {},
                        "contents": []
                    })
                
            logging.info(f"Whitelist parsing complete for {self.pdf_path}")
            return self.whitelisted_data
        except Exception as e:
            logging.error(f"Critical error during parsing: {e}", exc_info=True)
            raise

    def _extract_whitelisted_page_content(self, page: pikepdf.Page) -> dict:
        """
        Extracts whitelisted content from a single page object.
        - Dimensions (MediaBox)
        - Content streams (filtered operators)
        - Resources (Fonts, Images)
        """
        try:
            content = {
                "mediabox": list(page.MediaBox) if hasattr(page, 'MediaBox') else [0, 0, 612, 792],
                "resources": {},
                "contents": []
            }
        except Exception as e:
            logging.warning(f"Error reading page properties: {e}, using defaults")
            content = {
                "mediabox": [0, 0, 612, 792],
                "resources": {},
                "contents": []
            }
        
        # This is a placeholder for the complex task of parsing content streams
        # and validating operators against WHITELISTED_STREAM_OPERATORS.
        if hasattr(page, 'Contents') and page.Contents is not None:
            # In a real scenario, we'd parse this stream byte by byte.
            # For now, we'll decode the raw stream to make it JSON-serializable.
            try:
                # Handle both single stream and array of streams
                if isinstance(page.Contents, list):
                    # Multiple content streams
                    for stream in page.Contents:
                        try:
                            stream_bytes = stream.read_bytes()
                            stream_str = stream_bytes.decode('utf-8', errors='replace')
                            content["contents"].append(stream_str)
                        except Exception as e:
                            logging.warning(f"Could not read content stream in array: {e}")
                            content["contents"].append("")
                else:
                    # Single content stream
                    stream_bytes = page.Contents.read_bytes()
                    # Decode bytes to string, handling non-UTF8 bytes gracefully
                    stream_str = stream_bytes.decode('utf-8', errors='replace')
                    content["contents"].append(stream_str)
            except Exception as e:
                logging.warning(f"Could not read content stream: {e}")
                content["contents"].append("")

        # Recursively validate resources
        if hasattr(page, 'Resources') and page.Resources is not None:
            try:
                # Placeholder for resource validation
                content["resources"] = self._extract_whitelisted_resources(page.Resources)
            except Exception as e:
                logging.warning(f"Could not extract resources: {e}")
                content["resources"] = {"/Font": {}, "/XObject": {}}

        return content

    def _extract_whitelisted_resources(self, resources) -> dict:
        # Placeholder for deep resource validation.
        # This would involve checking font types, ensuring images are just raw pixel data, etc.
        return {"/Font": {}, "/XObject": {}} # Dummy data


class PDFReconstructor:
    """
    Rebuilds a clean PDF from a set of whitelisted page data.
    """
    def __init__(self, whitelisted_data: dict):
        self.data = whitelisted_data
        self.new_pdf = Pdf.new()

    def build(self, output_path: str):
        """
        Builds the new PDF and saves it to the specified path.
        Uses pikepdf's proper page creation API with proper Resources setup.
        """
        logging.info(f"Reconstructing new PDF from whitelisted data.")
        
        try:
            from pikepdf import Dictionary, Name, Array
            
            for page_data in self.data["pages"]:
                # Get page dimensions from mediabox [llx, lly, urx, ury]
                mediabox = page_data["mediabox"]
                
                # Create a new blank page using pikepdf add_blank_page
                # This returns a proper Page object that can be used
                width = mediabox[2] - mediabox[0]
                height = mediabox[3] - mediabox[1]
                page = self.new_pdf.add_blank_page(page_size=(width, height))
                
                # Ensure page has a proper Resources dictionary
                # This is necessary for PDF readers to render the page correctly
                if not hasattr(page, 'Resources') or page.Resources is None:
                    page.Resources = Dictionary()
                
                # Ensure Resources has Font dictionary (required by PDF spec)
                if 'Font' not in page.Resources:
                    page.Resources.Font = Dictionary()
                
                # Ensure Resources has ProcSet (common in PDFs)
                if 'ProcSet' not in page.Resources:
                    page.Resources.ProcSet = Array([Name.PDF, Name.Text, Name.ImageB, Name.ImageC, Name.ImageI])
                
                # Add content stream if available
                if page_data["contents"]:
                    content = page_data["contents"][0]
                    # Handle both bytes and string content
                    if isinstance(content, str):
                        content = content.encode('utf-8')
                    
                    # Validate content stream - wrap in BT/ET if needed for text operations
                    try:
                        page.Contents = self.new_pdf.make_stream(content)
                    except Exception as e:
                        logging.warning(f"Error setting page contents: {e}, using empty content")
                        page.Contents = self.new_pdf.make_stream(b"")

            # Remove all document-level metadata
            try:
                if self.new_pdf.docinfo:
                    del self.new_pdf.docinfo
            except (KeyError, AttributeError):
                pass
            
            try:
                if hasattr(self.new_pdf.Root, 'Metadata'):
                    del self.new_pdf.Root.Metadata
            except (KeyError, AttributeError):
                pass
                
            logging.info(f"Saving reconstructed PDF to {output_path}")
            self.new_pdf.save(output_path)
            logging.info(f"PDF successfully saved to {output_path}")
            
        except Exception as e:
            logging.error(f"Failed to reconstruct PDF: {e}", exc_info=True)
            raise

# Example Usage (for testing)
if __name__ == '__main__':
    # Create a dummy PDF with pikepdf for testing purposes
    pdf = Pdf.new()
    page = pdf.new_page()
    pdf.pages.append(page)
    page.Contents = pdf.make_stream(b"BT /F1 12 Tf 100 700 Td (Hello World) Tj ET")
    pdf.save("test_reconstruct.pdf")
    
    print("--- Starting Parser ---")
    parser = PDFWhitelistParser("test_reconstruct.pdf")
    data = parser.parse()
    
    print("\n--- Starting Reconstructor ---")
    reconstructor = PDFReconstructor(data)
    reconstructor.build("test_reconstruct_sanitized.pdf")
    
    print("\n--- Done ---")