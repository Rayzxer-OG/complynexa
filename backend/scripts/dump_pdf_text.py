"""
Dump extracted text from a PDF for debugging certificate parsing.

Usage (from backend folder, with venv activated):
  python scripts/dump_pdf_text.py "C:\path\to\your\Testing Report.pdf"

Uses pypdf for a quick dump. The app uses AWS Textract for actual processing;
if dates still don't extract, run the app and check logs, or use Textract
directly to see the exact text the app receives.
"""
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/dump_pdf_text.py <path-to-pdf>")
        sys.exit(1)
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    from pypdf import PdfReader
    reader = PdfReader(str(path))
    print(f"Total pages: {len(reader.pages)}\n")

    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        print(f"========== PAGE {i + 1} ==========")
        print(text)
        print()

if __name__ == "__main__":
    main()
