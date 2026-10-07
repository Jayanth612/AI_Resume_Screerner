import os
from docx import Document
import pdfplumber
from app.core.nlp_manager import NLPManager


class IngestionError(Exception):
    pass


def extract_text_from_docx(file_path: str) -> str:
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF, with OCR fallback for image-based PDFs"""
    text = ""

    try:
        # First try regular text extraction
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        # If we got substantial text, return it
        if text.strip() and len(text.strip()) > 50:
            print(f"[Ingestion] Extracted {len(text.strip())} chars from text-based PDF")
            return text.strip()
        
        # If no text or very little text, try OCR
        print("[Ingestion] No text found, attempting OCR...")
        return extract_text_with_ocr(file_path)
        
    except Exception as e:
        error_msg = str(e)
        
        # Check for corrupted PDF
        if "No /Root object" in error_msg or "trailer dictionary" in error_msg:
            print(f"[Ingestion] Corrupted PDF detected: {error_msg}")
            raise IngestionError("PDF file is corrupted or invalid. Please re-save or re-export the PDF.")
        
        print(f"[Ingestion] PDF extraction error: {e}")
        
        # Try OCR as fallback only if it's not a corruption issue
        try:
            return extract_text_with_ocr(file_path)
        except Exception as ocr_error:
            print(f"[Ingestion] OCR also failed: {ocr_error}")
            return ""


def extract_text_with_ocr(file_path: str) -> str:
    """Extract text from image-based PDF using OCR with optimizations"""
    try:
        from pdf2image import convert_from_path
        import pytesseract
        from concurrent.futures import ThreadPoolExecutor
        
        print("[Ingestion] Converting PDF to images...")
        # Reduce DPI for faster processing (200 is usually sufficient for text)
        images = convert_from_path(file_path, dpi=200, fmt='jpeg', thread_count=2)
        
        print(f"[Ingestion] Running OCR on {len(images)} pages...")
        
        # Parallel OCR processing for multi-page documents
        def ocr_page(page_data):
            i, image = page_data
            # Use faster PSM mode and optimize config
            custom_config = r'--oem 3 --psm 6'  # PSM 6 = assume uniform block of text
            page_text = pytesseract.image_to_string(image, lang='eng', config=custom_config)
            print(f"[Ingestion] Page {i+1}/{len(images)} processed")
            return page_text
        
        # Process pages in parallel (up to 4 at a time for OCR)
        with ThreadPoolExecutor(max_workers=min(4, len(images))) as executor:
            page_texts = list(executor.map(ocr_page, enumerate(images)))
        
        text = "\n".join(page_texts)
        return text.strip()
        
    except ImportError as e:
        raise IngestionError(
            "OCR libraries not installed. Install with: pip install pdf2image pytesseract pillow\n"
            "Also install Tesseract OCR: brew install tesseract (macOS) or apt-get install tesseract-ocr (Linux)"
        )
    except Exception as e:
        raise IngestionError(f"OCR extraction failed: {str(e)}")


def ingestion_stage(file_path: str) -> dict:
    if not os.path.exists(file_path):
        raise IngestionError("File not found")

    extension = os.path.splitext(file_path)[1].lower()

    if extension not in [".pdf", ".docx"]:
        raise IngestionError(f"Unsupported file format: {extension}")

    # -------- Text Extraction --------
    try:
        if extension == ".pdf":
            raw_text = extract_text_from_pdf(file_path)
        else:
            raw_text = extract_text_from_docx(file_path)
    except Exception as e:
        raise IngestionError(f"Text extraction failed: {str(e)}")

    # -------- Sanity Checks --------
    if not raw_text:
        raise IngestionError("Resume contains no extractable text. If this is an image-based PDF, please install OCR libraries.")

    cleaned_text = raw_text.strip()

    if len(cleaned_text) < 30:
        raise IngestionError("Extracted text too short or unreadable")

    print(f"[Ingestion] Extracted length: {len(cleaned_text)}")

    # -------- NLP Parsing (Single Parse Only) --------
    try:
        nlp = NLPManager.get_spacy()
        doc = nlp(cleaned_text)
    except Exception as e:
        raise IngestionError(f"NLP parsing failed: {str(e)}")

    return {
        "file_path": file_path,
        "raw_text": cleaned_text,
        "doc": doc
    }