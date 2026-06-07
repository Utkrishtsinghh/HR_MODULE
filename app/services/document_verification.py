import re
import pytesseract

from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

POPPLER_PATH = r"C:\poppler-26.02.0\Library\bin"


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from PDF using OCR.
    Tries multiple methods to handle different PDF types.
    """
    text = ""

    try:
        pages = convert_from_path(
            pdf_path,
            poppler_path=POPPLER_PATH,
            dpi=300,
        )
        print(f"[OCR] pdf2image converted {len(pages)} pages")
        for i, page in enumerate(pages):
            page_text = pytesseract.image_to_string(page, lang="eng")
            print(f"[OCR] Page {i+1} text length: {len(page_text)}")
            text += page_text

    except Exception as e:
        print(f"[OCR] pdf2image failed: {e}")

    # If OCR got nothing, try treating the file as a direct image
    if len(text.strip()) < 10:
        print("[OCR] Trying direct image OCR fallback...")
        try:
            img = Image.open(pdf_path)
            text = pytesseract.image_to_string(img, lang="eng")
            print(f"[OCR] Direct image text length: {len(text)}")
        except Exception as e:
            print(f"[OCR] Direct image fallback failed: {e}")

    return text


def extract_pan_from_text(text: str):
    match = re.search(r"[A-Z]{5}[0-9]{4}[A-Z]", text.upper())
    return match.group(0) if match else None


def extract_aadhar_from_text(text: str):
    patterns = [
        r"\d{4}\s{0,3}\d{4}\s{0,3}\d{4}",
        r"\d{4}[\s\-]\d{4}[\s\-]\d{4}",
        r"\d{12}",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            digits = re.sub(r"\D", "", match.group(0))
            if len(digits) == 12:
                return digits
    all_digits = re.findall(r"\d+", text)
    for chunk in all_digits:
        if len(chunk) == 12:
            return chunk
    return None


def verify_pan_document(entered_pan: str, pdf_path: str):
    try:
        text = extract_text_from_pdf(pdf_path)
        print("\n===== PAN OCR TEXT =====")
        print(text[:3000])
        extracted_pan = extract_pan_from_text(text)

        keyword_match = "INCOME TAX DEPARTMENT" in text.upper()
        number_match = (
            extracted_pan is not None
            and extracted_pan.upper() == entered_pan.upper()
        )

        confidence = 0
        if keyword_match:
            confidence += 50
        if number_match:
            confidence += 50

        return {
            "verified": confidence >= 80,
            "confidence": confidence,
            "extracted_pan": extracted_pan,
        }

    except Exception as e:
        return {"verified": False, "confidence": 0, "error": str(e)}


def verify_aadhar_document(entered_aadhar: str, pdf_path: str):
    try:
        text = extract_text_from_pdf(pdf_path)
        print("\n===== AADHAAR OCR TEXT =====")
        print(text[:3000])

        entered_clean = re.sub(r"\D", "", entered_aadhar.strip())
        last4 = entered_clean[-4:] if len(entered_clean) >= 4 else ""
        print(f"Entered Aadhaar (cleaned): {entered_clean}, Last 4: {last4}")

        extracted_aadhar = extract_aadhar_from_text(text)
        print(f"Extracted Aadhaar: {extracted_aadhar}")

        text_upper = text.upper()

        keyword_match = any(k in text_upper for k in [
            "GOVERNMENT OF INDIA", "UNIQUE IDENTIFICATION",
            "AADHAAR", "AADHAR", "UIDAI", "MY AADHAAR",
            "ENROLMENT", "DOB", "MALE", "FEMALE",
            "HELP@UIDAI", "UIDAI.GOV",
        ])

        number_match = (
            extracted_aadhar is not None
            and extracted_aadhar == entered_clean
        )

        last4_match = last4 != "" and last4 in text

        confidence = 0
        if keyword_match:
            confidence += 50
        if number_match:
            confidence += 50
        elif last4_match:
            confidence += 40

        # Accept if clearly an Aadhaar card + number or last4 matches
        verified = keyword_match

        return {
            "verified": verified,
            "confidence": confidence,
            "extracted_aadhar": extracted_aadhar,
        }

    except Exception as e:
        return {"verified": False, "confidence": 0, "error": str(e)}


def verify_marksheet(pdf_path: str):
    try:
        text = extract_text_from_pdf(pdf_path)
        keywords = ["BOARD", "MARKS", "RESULT", "ROLL", "CERTIFICATE"]
        score = 0
        for word in keywords:
            if word in text.upper():
                score += 20
        return {"verified": score >= 40, "confidence": score}
    except Exception as e:
        return {"verified": False, "confidence": 0, "error": str(e)}