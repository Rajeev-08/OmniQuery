from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.services.vector_service import vector_service

router = APIRouter(prefix="/upload", tags=["Document Ingestion"])

@router.post("")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Asynchronously ingests a file, processes it into semantic token chunks,
    generates local BGE embeddings, and populates the pgvector storage layer.
    """
    # 1. Read file contents safely
    try:
        contents = await file.read()
        raw_text = contents.decode("utf-8")
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Failed to read text contents from upload file. Ensure it is UTF-8 encoded. Error: {str(e)}"
        )

    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="Uploaded file content is entirely empty.")

    # 2. Hand off processing task to the Vector Ingestion Service
    try:
        total_chunks_created = vector_service.ingest_document(
            db=db,
            file_name=file.filename,
            file_type=file.content_type or "text/plain",
            raw_text=raw_text
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal database vector ingestion failure: {str(e)}"
        )

    return {
        "status": "success",
        "file_name": file.filename,
        "chunks_ingested": total_chunks_created,
        "message": f"Successfully processed and committed {total_chunks_created} vectors to pgvector."
    }