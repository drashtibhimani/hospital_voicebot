from fastapi import APIRouter, File, UploadFile

from backend.models import KnowledgeBaseUploadResponse
from backend.services.knowledgebase_service import save_and_ingest_upload


router = APIRouter()


@router.post("/upload", response_model=KnowledgeBaseUploadResponse)
async def upload_knowledgebase_file(
    file: UploadFile = File(...),
) -> KnowledgeBaseUploadResponse:
    result = await save_and_ingest_upload(file)
    return KnowledgeBaseUploadResponse(
        filename=str(result["filename"]),
        stored_path=str(result["stored_path"]),
        chunks_added=int(result["chunks_added"]),
        message="File uploaded and indexed successfully.",
    )
