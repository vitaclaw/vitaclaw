#!/usr/bin/env python3
"""Extract text from a PDF file using pdfplumber and output JSON."""

import sys
import json


def extract(pdf_path: str) -> dict:
    try:
        import pdfplumber
    except ImportError:
        return {"success": False, "error": "pdfplumber is not installed. Run: uv pip install pdfplumber"}

    try:
        pages_text = []
        with pdfplumber.open(pdf_path) as pdf:
            num_pages = len(pdf.pages)
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)
                else:
                    pages_text.append("")

        full_text = "\n---PAGE---\n".join(pages_text)
        has_text = any(t.strip() for t in pages_text)

        result = {
            "success": True,
            "pages": num_pages,
            "text": full_text if has_text else "",
        }
        if not has_text:
            result["image_only"] = True

        return result

    except Exception as e:
        return {"success": False, "error": str(e)}


def main() -> None:
    if len(sys.argv) < 2:
        print(
            json.dumps({"success": False, "error": "Usage: python3 extract_pdf.py [pdf_path]"}),
            flush=True,
        )
        sys.exit(1)

    pdf_path = sys.argv[1]
    result = extract(pdf_path)
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
