import os
from typing import List
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

class EmbeddingEngine:
    def __init__(self):
        # Using bge-small-en-v1.5 which maps perfectly to our 384-dimension vector column
        # The model automatically caches locally inside your environment on first run
        print("Loading local BGE Embedding Model...")
        self.model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        print("Embedding Model loaded successfully!")

    def chunk_text(self, text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
        """
        Splits raw documents recursively by characters (paragraphs, sentences, words)
        using token-length approximations to maintain dense semantic context blocks.
        """
        splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            model_name="gpt-3.5-turbo", # Using standard tiktoken encoder sizing
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        return splitter.split_text(text)

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Converts list of text strings into normalized vector lists ready for pgvector storage.
        """
        # Normalizing embeddings ensures we can run lightning-fast Cosine Similarity queries
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

# Instantiate as a singleton to avoid reloading the model weights multiple times across the application lifecycle
embedding_engine = EmbeddingEngine()