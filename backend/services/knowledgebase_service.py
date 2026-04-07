import re
import zipfile
from pathlib import Path
from uuid import uuid4
from xml.etree import ElementTree

from fastapi import HTTPException, UploadFile
from langchain_text_splitters import CharacterTextSplitter
from pypdf import PdfReader

from backend.services.rag_service import CHROMA_DIRECTORY, get_vectorstore


KNOWLEDGE_DIR = Path("backend/knowledge")
UPLOADS_DIR = KNOWLEDGE_DIR / "uploads"
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def ensure_knowledge_directories() -> None:
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    Path(CHROMA_DIRECTORY).mkdir(parents=True, exist_ok=True)


def _safe_filename(filename: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", filename).strip("._")
    return cleaned or "knowledge_file"


def _extract_pdf_text(file_path: Path) -> str:
    reader = PdfReader(str(file_path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(page.strip() for page in pages if page.strip())


def _extract_docx_text(file_path: Path) -> str:
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(file_path) as docx_file:
        document_xml = docx_file.read("word/document.xml")

    root = ElementTree.fromstring(document_xml)
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", namespace):
        text_parts = [
            node.text.strip()
            for node in paragraph.findall(".//w:t", namespace)
            if node.text and node.text.strip()
        ]
        if text_parts:
            paragraphs.append("".join(text_parts))

    return "\n".join(paragraphs)


def extract_text_from_path(file_path: Path) -> str:
    extension = file_path.suffix.lower()
    if extension == ".pdf":
        return _extract_pdf_text(file_path)
    if extension == ".docx":
        return _extract_docx_text(file_path)
    if extension == ".txt":
        return file_path.read_text(encoding="utf-8")
    raise ValueError(f"Unsupported file type: {extension}")


def ingest_text_content(text: str, source_name: str) -> int:
    splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.create_documents(
        [text],
        metadatas=[{"source": source_name}],
    )
    if not chunks:
        return 0

    vectorstore = get_vectorstore()
    vectorstore.add_documents(chunks)
    if hasattr(vectorstore, "persist"):
        vectorstore.persist()
    return len(chunks)


def ingest_path(file_path: Path, source_name: str | None = None) -> int:
    text = extract_text_from_path(file_path).strip()
    if not text:
        return 0
    return ingest_text_content(text, source_name or file_path.name)


async def save_and_ingest_upload(file: UploadFile) -> dict[str, str | int]:
    ensure_knowledge_directories()

    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename.")

    original_name = _safe_filename(file.filename)
    extension = Path(original_name).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, DOCX, and TXT files are supported.",
        )

    stored_name = f"{Path(original_name).stem}_{uuid4().hex}{extension}"
    destination = UPLOADS_DIR / stored_name

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    destination.write_bytes(file_bytes)

    try:
        chunk_count = ingest_path(destination, source_name=original_name)
    except Exception as error:
        destination.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail=f"Failed to process uploaded file: {error}",
        ) from error

    if chunk_count == 0:
        destination.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail="No readable text was found in the uploaded file.",
        )

    return {
        "filename": original_name,
        "stored_path": str(destination),
        "chunks_added": chunk_count,
    }
