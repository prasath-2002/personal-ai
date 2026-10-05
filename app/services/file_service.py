import re
from pathlib import Path
from uuid import uuid4

from pypdf import PdfReader
from app.core.config import DATA_DIR

UPLOAD_DIR = DATA_DIR / "uploads"


def save_uploaded_file(session_id: str, filename: str, content: bytes) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", session_id):
        raise ValueError("Invalid session ID")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_path = UPLOAD_DIR / f"{uuid4().hex}{Path(filename).suffix.lower()}"
    file_path.write_bytes(content)
    return file_path


def extract_text_from_file(file_path: Path) -> str:
    try:
        if file_path.suffix == ".txt":
            return file_path.read_text(encoding="utf-8-sig")
        if file_path.suffix == ".pdf":
            reader = PdfReader(str(file_path))
            if reader.is_encrypted:
                raise ValueError("Password-protected PDFs are not supported")
            return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as error:
        raise ValueError("Unable to read file. Use a valid text PDF or UTF-8 TXT file.") from error
    raise ValueError("Unsupported file type")


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    if chunk_size <= 0 or not 0 <= overlap < chunk_size:
        raise ValueError("Chunk size must be positive and overlap smaller than chunk size")
    text = text.strip()
    chunks = []
    for start in range(0, len(text), chunk_size - overlap):
        chunks.append(text[start:start + chunk_size])
        if start + chunk_size >= len(text):
            break
    return chunks
