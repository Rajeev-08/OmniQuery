from sqlalchemy.orm import Session
from app.models.vector_store import UserDocument, DocumentChunk
from app.services.embedding_service import embedding_engine

class VectorService:
    @staticmethod
    def ingest_document(db: Session, user_id: int, file_name: str, file_type: str, raw_text: str) -> int:
        chunks = embedding_engine.chunk_text(raw_text)
        if not chunks:
            return 0

        db_doc = UserDocument(user_id=user_id, file_name=file_name, file_type=file_type)
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)

        embeddings = embedding_engine.generate_embeddings(chunks)

        db_chunks = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            db_chunk = DocumentChunk(
                document_id=db_doc.id,
                content=chunk,
                embedding=embedding,
                metadata_tags={"chunk_index": i, "total_chunks": len(chunks)}
            )
            db_chunks.append(db_chunk)

        db.add_all(db_chunks)
        db.commit()
        return len(db_chunks)

vector_service = VectorService()