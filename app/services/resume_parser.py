from pathlib import Path
import re

import docx2txt
from pdfminer.high_level import extract_text


def parse_resume(file_path: str) -> str:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return extract_text(str(path))

    if suffix in {".docx", ".doc"}:
        return docx2txt.process(str(path))

    return path.read_text(errors="ignore")


def extract_email(text: str):
    match = re.search(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        text
    )

    return match.group(0) if match else None


def extract_phone(text: str):
    match = re.search(
        r"(\+?\d[\d\s\-]{8,15}\d)",
        text
    )

    return match.group(0) if match else None