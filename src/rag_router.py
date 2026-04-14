import shutil
import tempfile
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from .rag_service import RAGService

router = APIRouter(prefix="/rag", tags=["RAG"])
rag_service = RAGService()


class QueryRequest(BaseModel):
    question: str
    k: int = 4
    return_sources: bool = True


@router.post("/ingest")
async def ingest_file(file: UploadFile = File(...)):
    allowed_types = ["application/pdf", "text/plain", "text/markdown"]
    if file.content_type not in allowed_types:
        raise HTTPException(400, f"Tipo file non supportato: {file.content_type}")
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
    try:
        return rag_service.ingest_documents(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@router.post("/query")
async def query(request: QueryRequest):
    try:
        return rag_service.query(question=request.question, k=request.k, return_sources=request.return_sources)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/stats")
async def stats():
    return rag_service.get_stats()
