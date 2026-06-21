import io
import re

from src.logger import get_logger

logger = get_logger(__name__)

# Common Tesseract install path on Windows
_TESSERACT_WIN = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def _try_ocr(file_bytes: bytes) -> str:
    """Render PDF pages to images and OCR them with EasyOCR (no external binary needed)."""
    try:
        import fitz  # pymupdf
        import easyocr
        import numpy as np

        # Use default detector — craft-text-detector is optional; easyocr falls back gracefully
        reader = easyocr.Reader(["en"], verbose=False)
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        pages_text = []
        for page in doc:
            mat = fitz.Matrix(2, 2)  # 2x zoom for better OCR accuracy
            pix = page.get_pixmap(matrix=mat)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
            result = reader.readtext(img, detail=0, paragraph=True)
            pages_text.append("\n".join(result))
        doc.close()
        return "\n".join(pages_text)
    except Exception as exc:
        logger.warning("OCR extraction failed: %s", exc)
        return ""


def extract_text_from_pdf(file_bytes: bytes) -> str:
    # Try pdfminer first — best for text-based PDFs
    try:
        from pdfminer.high_level import extract_text
        text = extract_text(io.BytesIO(file_bytes))
        if text and len(text.strip()) > 50:
            return text
    except Exception as exc:
        logger.warning("pdfminer extraction failed: %s", exc)

    # Fallback 1: pypdf
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages)
        if text and len(text.strip()) > 50:
            return text
    except Exception as exc:
        logger.warning("pypdf extraction failed: %s", exc)

    # Fallback 2: OCR via pymupdf + Tesseract
    logger.info("No text layer found in PDF — attempting OCR...")
    text = _try_ocr(file_bytes)
    return text


def extract_text_from_docx(file_bytes: bytes) -> str:
    try:
        from docx import Document

        doc = Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as exc:
        logger.warning("DOCX text extraction failed: %s", exc)
        return ""


def extract_resume_text(file_bytes: bytes, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "pdf":
        raw = extract_text_from_pdf(file_bytes)
    elif ext == "docx":
        raw = extract_text_from_docx(file_bytes)
    else:
        raise ValueError(f"Unsupported file type '.{ext}'. Upload a PDF or DOCX.")

    return re.sub(r"\s+", " ", raw).strip()
