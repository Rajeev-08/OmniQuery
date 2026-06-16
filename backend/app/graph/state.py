from typing import List, TypedDict

class GraphState(TypedDict):
    user_id: int
    question: str
    generation: str
    search_fallback: bool
    documents: List[dict]
    steps: List[str]