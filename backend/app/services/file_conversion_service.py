"""Convert supported document/image formats to PDF for Textract and storage."""

import io
import logging
import os
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

# Image extensions supported by PIL and acceptable for PDF conversion
_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".tiff", ".bmp")
# Office/document formats converted via LibreOffice headless
_LIBREOFFICE_EXTENSIONS = (".docx", ".doc", ".xlsx", ".xls", ".txt")


def convert_to_pdf(file_bytes: bytes, filename: str) -> bytes:
    """
    Convert file to PDF. Returns bytes unchanged if already PDF.
    Raises ValueError for unsupported format.
    """
    filename = (filename or "").lower()

    if filename.endswith(".pdf"):
        return file_bytes

    if filename.endswith(_IMAGE_EXTENSIONS):
        return _image_to_pdf(file_bytes)

    if filename.endswith(_LIBREOFFICE_EXTENSIONS):
        return _libreoffice_to_pdf(file_bytes, filename)

    raise ValueError("Unsupported conversion")


def _image_to_pdf(file_bytes: bytes) -> bytes:
    """Convert image bytes to a single-page PDF using Pillow."""
    from PIL import Image

    image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    pdf_buffer = io.BytesIO()
    image.save(pdf_buffer, format="PDF")
    return pdf_buffer.getvalue()


def _libreoffice_to_pdf(file_bytes: bytes, filename: str) -> bytes:
    """Convert document to PDF using LibreOffice headless. Requires LibreOffice installed."""
    ext = Path(filename).suffix.lower()
    out_dir = tempfile.gettempdir()
    fd, input_path = tempfile.mkstemp(suffix=ext, dir=out_dir)
    try:
        try:
            os.write(fd, file_bytes)
        finally:
            os.close(fd)
        result = subprocess.run(
            [
                "libreoffice",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                out_dir,
                input_path,
            ],
            capture_output=True,
            timeout=120,
            check=False,
        )
        if result.returncode != 0:
            logger.warning(
                "LibreOffice convert failed: %s %s",
                result.stderr.decode("utf-8", errors="replace") if result.stderr else "",
                result.stdout.decode("utf-8", errors="replace") if result.stdout else "",
            )
            raise ValueError("Document conversion failed")
        output_name = Path(input_path).stem + ".pdf"
        output_path = Path(out_dir) / output_name
        if not output_path.exists():
            raise ValueError("Conversion did not produce a PDF")
        return output_path.read_bytes()
    finally:
        for p in (input_path, Path(out_dir) / (Path(input_path).stem + ".pdf")):
            if isinstance(p, str):
                path = Path(p)
            else:
                path = p
            if path.exists():
                try:
                    path.unlink()
                except OSError as e:
                    logger.warning("Failed to remove temp file %s: %s", path, e)
