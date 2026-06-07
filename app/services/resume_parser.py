from pathlib import Path
import re

import docx2txt
from pdfminer.high_level import extract_text


def parse_resume(file_path: str) -> str:
    path = Path(file_path)
    suffix = path.suffix.lower()

    try:
        if suffix == ".pdf":
            return extract_text(str(path))

        if suffix in {".docx", ".doc"}:
            return docx2txt.process(str(path))

        return path.read_text(errors="ignore")

    except Exception as e:
        print("Resume Parse Error:", e)
        return ""


def extract_email(text: str):

    # Remove spaces/newlines that OCR or PDF extraction may introduce
    cleaned_text = (
        text.replace("\n", " ")
            .replace("\r", " ")
    )

    matches = re.findall(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
        cleaned_text
    )

    if matches:

        # Return first valid email found
        return matches[0].strip().lower()

    return None


def extract_phone(text: str):

    cleaned_text = (
        text.replace("\n", " ")
            .replace("\r", " ")
    )

    matches = re.findall(
        r'(?:\+91[\-\s]?)?[6-9]\d{9}',
        cleaned_text
    )

    if matches:
        return matches[0]

    return None