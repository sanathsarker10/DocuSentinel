from pathlib import Path
from io import BytesIO
import fitz
from PIL import Image
from ocr_utils import extract_text_from_image, extract_text_from_pdf
from forensic_checks import image_forensic_checks, make_ela_visualization

MAX_FILE_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}


def analyze_document(filename: str, raw: bytes) -> dict:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file type.")
    if len(raw) > MAX_FILE_BYTES:
        raise ValueError("File exceeds the 10 MB limit.")
    if not raw:
        raise ValueError("The uploaded file is empty.")

    findings = []
    metadata = {
        "filename": Path(filename).name,
        "file_extension": suffix,
        "file_size_bytes": len(raw),
    }
    extracted_text = ""
    pages_analyzed = 1
    ela_image = None

    if suffix == ".pdf":
        try:
            doc = fitz.open(stream=raw, filetype="pdf")
        except Exception as exc:
            raise ValueError("Could not read this PDF. It may be damaged or invalid.") from exc

        if doc.is_encrypted:
            doc.close()
            raise ValueError("Password-protected PDFs are not supported in this prototype.")
        if len(doc) == 0:
            doc.close()
            raise ValueError("The PDF has no pages.")
        if len(doc) > 20:
            doc.close()
            raise ValueError("Please upload a PDF with 20 pages or fewer.")

        pages_analyzed = len(doc)
        md = doc.metadata or {}
        metadata["pdf_metadata"] = {
            "title": md.get("title"),
            "author": md.get("author"),
            "creator": md.get("creator"),
            "producer": md.get("producer"),
            "creation_date": md.get("creationDate"),
            "modification_date": md.get("modDate"),
            "page_count": len(doc),
            "has_embedded_signatures": "Not reliably determined by this prototype",
        }
        extracted_text = extract_text_from_pdf(doc)
        if not extracted_text.strip():
            extracted_text = extract_text_from_pdf(doc, use_ocr=True)
        if md.get("creationDate") and md.get("modDate") and md.get("creationDate") != md.get("modDate"):
            findings.append({
                "title": "PDF creation and modification dates differ",
                "severity": "Low",
                "details": "The metadata reports different creation and modification dates. This is common in legitimate workflows and is not proof of tampering.",
                "recommendation": "Review the document's history or verify it with the issuer if the dates are relevant."
            })
        # Analyze first page for a basic visual screening image.
        pix = doc[0].get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
        first_page_image = Image.open(BytesIO(pix.tobytes("png"))).convert("RGB")
        doc.close()
        findings.extend(image_forensic_checks(first_page_image))
        ela_image = make_ela_visualization(first_page_image)
    else:
        try:
            image = Image.open(BytesIO(raw)).convert("RGB")
        except Exception as exc:
            raise ValueError("Could not read this image file.") from exc
        metadata["image_metadata"] = {
            "format": Image.open(BytesIO(raw)).format,
            "dimensions": list(image.size),
        }
        extracted_text = extract_text_from_image(image)
        findings.extend(image_forensic_checks(image))
        ela_image = make_ela_visualization(image)

    # Simple field consistency checks: these are useful only as prompts for review.
    lower_text = extracted_text.lower()
    if any(term in lower_text for term in ["sample", "specimen", "dummy document", "for testing"]):
        findings.append({
            "title": "Sample or test wording detected",
            "severity": "Low",
            "details": "The extracted text contains wording often used in sample documents. This can be intentional.",
            "recommendation": "Confirm whether this is a test document or an official submission."
        })
    if len(extracted_text.strip()) < 20:
        findings.append({
            "title": "Very little text was extracted",
            "severity": "Medium",
            "details": "OCR extracted fewer than 20 characters. This may be caused by poor image quality, handwriting, unusual fonts, or a non-text document.",
            "recommendation": "Use a clearer scan and verify the fields manually."
        })

    high_or_medium = any(f["severity"] in ("High", "Medium") for f in findings)
    overall_status = (
        "Manual review recommended — one or more indicators need attention."
        if high_or_medium else
        "No strong indicators found by the basic checks — authenticity remains unverified."
    )

    return {
        "findings": findings,
        "extracted_text": extracted_text[:20000],
        "metadata": metadata,
        "pages_analyzed": pages_analyzed,
        "overall_status": overall_status,
        "ela_image": ela_image,
    }
