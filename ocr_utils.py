from io import BytesIO
import fitz
import pytesseract
from PIL import Image


def extract_text_from_image(image: Image.Image) -> str:
    try:
        return pytesseract.image_to_string(image)
    except pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError(
            "Tesseract OCR is not installed. Install the Tesseract application and restart the app."
        ) from exc


def extract_text_from_pdf(doc: fitz.Document, use_ocr: bool = False) -> str:
    pieces = []
    for page in doc:
        text = page.get_text("text").strip()
        if text and not use_ocr:
            pieces.append(text)
            continue
        if use_ocr or not text:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image = Image.open(BytesIO(pix.tobytes("png"))).convert("RGB")
            pieces.append(extract_text_from_image(image))
    return "\n\n".join(pieces)
