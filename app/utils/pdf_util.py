import hashlib
import fitz


def read_pdf_text(file_bytes) -> list[str]:
    text_pages = []
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text = page.get_text()
            text_pages.append(text)
    return text_pages


def get_file_hash(file_content) -> str:
    if isinstance(file_content, list):
        return str(hashlib.sha256(" ".join(file_content).encode("utf-8")).hexdigest())
    elif isinstance(file_content, str):
        return str(hashlib.sha256(file_content.encode("utf-8")).hexdigest())
    return str(hashlib.sha256(file_content).hexdigest())
