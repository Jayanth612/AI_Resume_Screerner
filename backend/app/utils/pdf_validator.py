"""
PDF validation utilities to check file integrity before processing
"""
import os
from pathlib import Path


def validate_pdf_file(file_path: str) -> tuple[bool, str]:
    """
    Validate PDF file before processing
    
    Returns:
        (is_valid, error_message)
    """
    
    # Check file exists
    if not os.path.exists(file_path):
        return False, "File not found"
    
    # Check file size
    file_size = os.path.getsize(file_path)
    if file_size == 0:
        return False, "File is empty"
    
    if file_size < 100:  # Less than 100 bytes is suspicious
        return False, "File is too small to be a valid PDF"
    
    # Check PDF header
    try:
        with open(file_path, 'rb') as f:
            header = f.read(5)
            if not header.startswith(b'%PDF-'):
                return False, "File does not have a valid PDF header"
    except Exception as e:
        return False, f"Cannot read file: {str(e)}"
    
    # Quick corruption check using pdfplumber
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            # Try to access basic properties
            num_pages = len(pdf.pages)
            if num_pages == 0:
                return False, "PDF has no pages"
            
            # Try to access first page
            first_page = pdf.pages[0]
            if first_page is None:
                return False, "Cannot access PDF pages"
                
    except Exception as e:
        error_msg = str(e)
        if "No /Root object" in error_msg or "trailer dictionary" in error_msg:
            return False, "PDF is corrupted or malformed"
        return False, f"PDF validation failed: {error_msg}"
    
    return True, "Valid PDF"


def get_pdf_info(file_path: str) -> dict:
    """
    Get basic PDF information
    
    Returns:
        dict with page_count, file_size, has_text
    """
    import pdfplumber
    
    info = {
        "page_count": 0,
        "file_size": os.path.getsize(file_path),
        "has_text": False,
        "estimated_ocr_time": 0
    }
    
    try:
        with pdfplumber.open(file_path) as pdf:
            info["page_count"] = len(pdf.pages)
            
            # Check if first page has text
            if pdf.pages:
                first_page_text = pdf.pages[0].extract_text()
                info["has_text"] = bool(first_page_text and len(first_page_text.strip()) > 50)
            
            # Estimate OCR time (if needed)
            if not info["has_text"]:
                # Rough estimate: 30-60 seconds per page at 200 DPI
                info["estimated_ocr_time"] = info["page_count"] * 45
                
    except Exception:
        pass
    
    return info
