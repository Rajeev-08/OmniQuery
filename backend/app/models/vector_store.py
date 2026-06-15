from sqlalchemy import Column, String, Text, Integer, JSON, DateTime, func
from pgvector.sqlalchemy import Vector
from app.core.db import Base

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), nullable=False, index=True)
    file_type = Column(String(50), nullable=False)
    
    # Raw processed chunk text payload
    content = Column(Text, nullable=False)
    
    # 384 dimensions matching local bge-small-en-v1.5 sentence-transformer model
    embedding = Column(Vector(384), nullable=False)
    
    # Metadata structural storage for parent-child hierarchies, page numbers, tags
    metadata_tags = Column(JSON, server_default="{}", nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())