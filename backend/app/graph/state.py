from typing import List, TypedDict

class GraphState(TypedDict):

    question: str                  # The initial user query
    generation: str                # The final synthesized LLM answer
    search_fallback: bool          # Flag to trigger web search if context grading fails
    documents: List[dict]          # List of retrieved document chunks from pgvector
    steps: List[str]               # Tracks system operational trace logs (for our UI timeline view)