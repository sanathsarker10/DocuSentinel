from io import BytesIO
from PIL import Image, ImageChops, ImageEnhance, ImageStat
import numpy as np


def image_forensic_checks(image: Image.Image) -> list:
    findings = []
    width, height = image.size
    if min(width, height) < 400:
        findings.append({
            "title": "Low image resolution",
            "severity": "Medium",
            "details": f"The image is {width} × {height} pixels. Small images can hide details and reduce OCR reliability.",
            "recommendation": "Use a higher-resolution scan or photograph with even lighting."
        })

    # Check for extreme image contrast/brightness; these are quality indicators, not fraud detection.
    gray = image.convert("L")
    stat = ImageStat.Stat(gray)
    mean_brightness = stat.mean[0]
    if mean_brightness < 45 or mean_brightness > 225:
        findings.append({
            "title": "Unusual overall brightness",
            "severity": "Low",
            "details": f"Average grayscale brightness is {mean_brightness:.1f}/255. Very dark or bright images can obscure content.",
            "recommendation": "Review the original and, if possible, capture a new scan under even lighting."
        })
    return findings


def make_ela_visualization(image: Image.Image):
    """Return a simple ELA visualization. It is not a forensic verdict."""
    try:
        image = image.convert("RGB")
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=90)
        buffer.seek(0)
        recompressed = Image.open(buffer).convert("RGB")
        diff = ImageChops.difference(image, recompressed)
        extrema = diff.getextrema()
        max_diff = max(channel[1] for channel in extrema)
        if max_diff > 0:
            diff = ImageEnhance.Contrast(diff).enhance(min(255 / max_diff, 10))
        # Resize large images for a lightweight UI preview.
        diff.thumbnail((1000, 1000))
        return diff
    except Exception:
        return None
