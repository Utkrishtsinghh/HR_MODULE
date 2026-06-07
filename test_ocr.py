from app.services.document_verification import extract_text_from_pdf

text = extract_text_from_pdf(
    r"uploads\documents\PAN Card.pdf"
)

print(text)