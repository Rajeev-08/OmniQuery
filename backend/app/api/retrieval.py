from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from app.core.db import get_db
from app.services.embedding_service import embedding_engine

router = APIRouter(prefix="/search", tags=["Vector Retrieval"])

@router.get("")
def hybrid_vector_search(query: str = Query(..., min_length=2), limit: int = 5, db: Session = Depends(get_db)):
    """
    Converts a string query to vector space using BGE, then runs a 
    native pgvector cosine distance match operator (<=>) over our chunks.
    """
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query text cannot be blank.")

    try:
        # 1. Vectorize user text using our local single-instance embedding model
        query_vector = embedding_engine.generate_embeddings([query])[0]
        
        # 2. Execute raw PostgreSQL Cosine Similarity matching (<=> calculates cosine distance)
        # Cosine Similarity = 1 - Cosine Distance
# 2. Execute raw PostgreSQL Cosine Similarity matching safely using CAST
        # This avoids the double-colon (::) syntax conflict with SQLAlchemy bindings
        sql_statement = text("""
            SELECT id, file_name, content, metadata_tags,
                   (1 - (embedding <=> CAST(:vector_payload AS vector))) AS similarity_score
            FROM document_chunks
            ORDER BY embedding <=> CAST(:vector_payload AS vector)
            LIMIT :limit_count;
        """)
        
        results = db.execute(
            sql_statement, 
            {"vector_payload": str(query_vector), "limit_count": limit}
        ).fetchall()

        # 3. Format result arrays cleanly
        formatted_matches = []
        for row in results:
            formatted_matches.append({
                "chunk_id": row.id,
                "file_name": row.file_name,
                "content": row.content,
                "metadata": row.metadata_tags,
                "similarity": round(float(row.similarity_score), 4)
            })

        return {
            "query": query,
            "total_matches": len(formatted_matches),
            "results": formatted_matches
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during vector table matching: {str(e)}"
        )