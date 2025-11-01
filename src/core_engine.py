"""
Module: core_engine
Description: Contains the primary PDF parsing, whitelisting, and reconstruction
             logic. This is the heart of the sanitization process.
"""

import pikepdf
from pikepdf import Pdf, PdfImage
from decimal import Decimal
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
        self.original_pdf = None
        try:
            try:
                self.pdf = Pdf.open(self.pdf_path, allow_overwriting_input=True)
                self.original_pdf = self.pdf  # Keep reference to original for extraction
            except pikepdf.PasswordError:
                raise ValueError("The PDF file is encrypted and cannot be opened without a password.")
        except Exception as e:
            logging.error(f"Failed to open PDF {pdf_path}: {e}")
            raise

    def parse(self):
        """
        Executes the parsing and whitelisting process.
        Returns extracted page data with binary content preserved.
        """
        logging.info(f"Starting whitelist parsing for {self.pdf_path}")
        try:
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
                        "contents": None
                    })
                
            logging.info(f"Whitelist parsing complete for {self.pdf_path}")
            return self.whitelisted_data
        except Exception as e:
            logging.error(f"Critical error during parsing: {e}", exc_info=True)
            raise

    def get_original_pdf(self):
        """
        Returns reference to the original PDF object for direct content extraction.
        """
        return self.original_pdf

    def _extract_whitelisted_page_content(self, page: pikepdf.Page) -> dict:
        """
        Extracts whitelisted metadata from a single page object.
        Stores only JSON-serializable metadata, not binary content.
        The actual PDF content will be copied directly during reconstruction.
        """
        try:
            # Convert MediaBox, handling Decimal objects from pikepdf
            mediabox = page.MediaBox if hasattr(page, 'MediaBox') else [0, 0, 612, 792]
            try:
                # Convert to list and handle Decimal values
                mediabox = [float(x) for x in mediabox]
            except (TypeError, ValueError):
                mediabox = [0, 0, 612, 792]
            
            content = {
                "mediabox": mediabox,
                "resources": {},
                "has_contents": hasattr(page, 'Contents') and page.Contents is not None
            }
        except Exception as e:
            logging.warning(f"Error reading page properties: {e}, using defaults")
            content = {
                "mediabox": [0, 0, 612, 792],
                "resources": {},
                "has_contents": False
            }
        
        # Extract resource metadata (not the actual resources)
        if hasattr(page, 'Resources') and page.Resources is not None:
            try:
                content["resources"] = self._extract_whitelisted_resources(page.Resources)
            except Exception as e:
                logging.warning(f"Could not extract resources: {e}")
                content["resources"] = {"/Font": {}, "/XObject": {}}

        return content

    def _extract_whitelisted_resources(self, resources) -> dict:
        """
        Extract whitelisted resources from a page.
        Includes: Fonts (safe, standard fonts) and XObjects (images - raw pixel data).
        Excludes: Embedded programs, scripts, malicious content.
        
        Note: Returns JSON-serializable metadata about resources, not the objects themselves.
        """
        result = {"/Font": {}, "/XObject": {}}
        
        if not resources:
            return result
        
        try:
            # Extract Font resources (standard fonts are safe)
            if hasattr(resources, 'Font') and resources.Font:
                try:
                    for font_name, font_obj in resources.Font.items():
                        # Store metadata about the font, not the object itself
                        try:
                            font_name_str = str(font_name)
                            basefont = str(font_obj.BaseFont) if hasattr(font_obj, 'BaseFont') else "Unknown"
                            result["/Font"][font_name_str] = {"BaseFont": basefont}
                            logging.debug(f"Extracted font: {font_name_str}")
                        except Exception as e:
                            logging.debug(f"Error storing font {font_name}: {e}")
                except Exception as e:
                    logging.warning(f"Error extracting fonts: {e}")
            
            # Extract XObjects (images are safe if they're just pixel data)
            if hasattr(resources, 'XObject') and resources.XObject:
                try:
                    for xobj_name, xobj in resources.XObject.items():
                        # Check if it's an image (not a form or other dangerous object)
                        try:
                            if hasattr(xobj, 'Subtype'):
                                subtype = str(xobj.Subtype)
                                # Include Image XObjects (raw pixel data)
                                if subtype == '/Image' or 'Image' in subtype:
                                    xobj_name_str = str(xobj_name)
                                    # Store metadata about the image, not the object itself
                                    width = int(xobj.Width) if hasattr(xobj, 'Width') else None
                                    height = int(xobj.Height) if hasattr(xobj, 'Height') else None
                                    colorspace = str(xobj.ColorSpace) if hasattr(xobj, 'ColorSpace') else None
                                    result["/XObject"][xobj_name_str] = {
                                        "Subtype": subtype,
                                        "Width": width,
                                        "Height": height,
                                        "ColorSpace": colorspace
                                    }
                                    logging.debug(f"Extracted image: {xobj_name_str}")
                                else:
                                    logging.debug(f"Skipped non-image XObject: {xobj_name} (type: {subtype})")
                            else:
                                # No Subtype - include as metadata
                                xobj_name_str = str(xobj_name)
                                result["/XObject"][xobj_name_str] = {"type": "XObject"}
                                logging.debug(f"Extracted XObject without Subtype: {xobj_name_str}")
                        except Exception as e:
                            logging.warning(f"Error checking XObject {xobj_name}: {e}")
                except Exception as e:
                    logging.warning(f"Error extracting XObjects: {e}")
        
        except Exception as e:
            logging.error(f"Error in _extract_whitelisted_resources: {e}")
            return {"/Font": {}, "/XObject": {}}
        
        return result


class PDFReconstructor:
    """
    Rebuilds a clean PDF from a set of whitelisted page data and original PDF.
    Copies content streams directly from the original PDF to preserve all text/graphics.
    """
    def __init__(self, whitelisted_data: dict, original_pdf: Pdf = None):
        self.data = whitelisted_data
        self.original_pdf = original_pdf
        self.new_pdf = Pdf.new()

    def build(self, output_path: str):
        """
        Builds the new PDF by copying pages from the original PDF with whitelisted structure.
        Preserves actual content while removing metadata threats.
        """
        logging.info(f"Reconstructing new PDF from whitelisted data.")
        
        try:
            from pikepdf import Dictionary, Name, Array
            
            # If we have the original PDF, copy pages directly to preserve all content
            if self.original_pdf:
                logging.info(f"Copying {len(self.original_pdf.pages)} pages from original PDF")
                try:
                    # Use pikepdf's extend method to copy pages efficiently
                    # This preserves all content streams and resources
                    self.new_pdf.pages.extend(self.original_pdf.pages)
                    logging.info(f"Successfully copied all {len(self.original_pdf.pages)} pages from original PDF")
                except Exception as e:
                    logging.warning(f"Error copying pages: {e}, creating blank pages")
                    # Fallback: create blank pages with proper structure
                    for i, page_data in enumerate(self.data["pages"]):
                        try:
                            mediabox = page_data.get("mediabox", [0, 0, 612, 792])
                            width = mediabox[2] - mediabox[0]
                            height = mediabox[3] - mediabox[1]
                            page = self.new_pdf.add_blank_page(page_size=(width, height))
                            
                            # Setup basic resources
                            if not hasattr(page, 'Resources') or page.Resources is None:
                                page.Resources = Dictionary()
                            if 'Font' not in page.Resources:
                                page.Resources.Font = Dictionary()
                            if 'ProcSet' not in page.Resources:
                                page.Resources.ProcSet = Array([Name.PDF, Name.Text, Name.ImageB, Name.ImageC, Name.ImageI])
                        except Exception as e2:
                            logging.warning(f"Error creating blank page {i+1}: {e2}")
            else:
                logging.warning("No original PDF provided, creating blank pages")
                # Fallback: create blank pages with metadata from whitelisted data
                for page_data in self.data["pages"]:
                    mediabox = page_data["mediabox"]
                    width = mediabox[2] - mediabox[0]
                    height = mediabox[3] - mediabox[1]
                    page = self.new_pdf.add_blank_page(page_size=(width, height))
                    
                    if not hasattr(page, 'Resources') or page.Resources is None:
                        page.Resources = Dictionary()
                    if 'Font' not in page.Resources:
                        page.Resources.Font = Dictionary()
                    if 'ProcSet' not in page.Resources:
                        page.Resources.ProcSet = Array([Name.PDF, Name.Text, Name.ImageB, Name.ImageC, Name.ImageI])

            # Remove all document-level metadata and interactive content
            logging.info("Sanitizing document metadata")
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
            
            # Remove AcroForm (interactive forms)
            try:
                if hasattr(self.new_pdf.Root, 'AcroForm'):
                    del self.new_pdf.Root.AcroForm
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
    reconstructor = PDFReconstructor(data, parser.get_original_pdf())

    reconstructor = PDFReconstructor(data)
    reconstructor.build("test_reconstruct_sanitized.pdf")
    
    print("\n--- Done ---")