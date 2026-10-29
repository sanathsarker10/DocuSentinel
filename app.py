import hashlib
import io
import re
from datetime import datetime

import fitz
import numpy as np
import streamlit as st
from PIL import Image, ImageChops, ImageEnhance, ImageStat, UnidentifiedImageError

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except Exception:
    TESSERACT_AVAILABLE = False

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

st.set_page_config(page_title="DocuSentinel | Document Forensics", page_icon="🛡️", layout="wide")

# ---------- Core utilities ----------
def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_text(value) -> str:
    if value is None:
        return "Not available"
    text = str(value).strip()
    return text if text else "Not available"


def extract_pdf(data: bytes):
    doc = PdfReader(io.BytesIO(data))
    metadata = doc.metadata or {}
    page_texts = []
    page_sizes = []
    for page in doc:
        page_texts.append(page.get_text("text") or "")
        rect = page.rect
        page_sizes.append(f"{rect.width:.0f} × {rect.height:.0f} pt")
    # Render first page for visual analysis. Limit resolution to keep the app responsive.
    first_page_image = None
    if len(doc) > 0:
        pix = doc[0].get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
        first_page_image = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
    details = {
        "File type": "PDF document",
        "Pages": len(doc),
        "PDF version": safe_text(metadata.get("format")),
        "Title": safe_text(metadata.get("title")),
        "Author": safe_text(metadata.get("author")),
        "Creator": safe_text(metadata.get("creator")),
        "Producer": safe_text(metadata.get("producer")),
        "Created": safe_text(metadata.get("creationDate")),
        "Modified": safe_text(metadata.get("modDate")),
        "Page sizes": ", ".join(sorted(set(page_sizes))) if page_sizes else "Not available",
        "Password protected": "Yes" if doc.is_encrypted else "No",
    }
    # Font inventory is a useful inspection clue, not proof of editing.
    fonts = set()
    for page in doc:
        try:
            for item in page.get_fonts(full=True):
                if len(item) > 3 and item[3]:
                    fonts.add(str(item[3]))
        except Exception:
            pass
    details["Font names detected"] = ", ".join(sorted(fonts)) if fonts else "No font names extracted"
    doc.close()
    return "\n\n".join(f"--- Page {i + 1} ---\n{text}" for i, text in enumerate(page_texts)), details, first_page_image


def extract_image(data: bytes):
    image = Image.open(io.BytesIO(data)).convert("RGB")
    details = {
        "File type": "Image document",
        "Dimensions": f"{image.width} × {image.height} pixels",
        "Color mode": image.mode,
        "Image format": "Decoded image",
    }
    try:
        original = Image.open(io.BytesIO(data))
        exif = original.getexif()
        details["EXIF fields"] = len(exif)
        software = exif.get(305)
        captured = exif.get(36867) or exif.get(306)
        details["EXIF software"] = safe_text(software)
        details["EXIF date"] = safe_text(captured)
    except Exception:
        details["EXIF fields"] = 0
        details["EXIF software"] = "Not available"
