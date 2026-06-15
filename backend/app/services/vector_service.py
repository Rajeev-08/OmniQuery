from sqlalchemy.orm import Session
from app.models.vector_store import DocumentChunk
from app.services.embedding_service import embedding_engine

class VectorService:
    @staticmethod
    def ingest_document(db: Session, file_name: str, file_type: str, raw_text: str) -> int:
        """
        Processes a raw document payload, splits it into semantic overlapping chunks, 
        vectorizes the text, and writes records directly to PostgreSQL.
        """
        # 1. Break text down into structural tokens
        chunks = embedding_engine.chunk_text(raw_text)
        if not chunks:
            return 0

        # 2. Vectorize the entire chunk collection in a single batch
        embeddings = embedding_engine.generate_embeddings(chunks)

        # 3. Create ORM models ready to be loaded to the database
        db_chunks = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            db_chunk = DocumentChunk(
                file_name=file_name,
                file_type=file_type,
                content=chunk,
                embedding=embedding,
                metadata_tags={
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            )
            db_chunks.append(db_chunk)

        # 4. Atomically commit the records to the database
        db.add_all(db_chunks)
        db.commit()
        
        return len(db_chunks)

vector_service = VectorService()