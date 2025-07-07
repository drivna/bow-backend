import hashlib
import fitz


def read_pdf_text(file_bytes) -> list[str]:
    text_pages = []
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text = page.get_text()
            text_pages.append(text)
    return text_pages


def get_file_hash(file_content: bytes) -> str:
    return hashlib.sha256(file_content).hexdigest()
