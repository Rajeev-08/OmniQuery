import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/omniquery_db")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Initializes the database and enables the pgvector extension."""
    with engine.begin() as conn:
        # Create pgvector extension if it doesn't exist
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    
    # Create all tables defined in our models
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency provider for FastAPI endpoint routes to inject DB sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()