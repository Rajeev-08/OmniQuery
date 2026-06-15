from langgraph.graph import StateGraph, END
from app.graph.state import GraphState
from app.graph.nodes import retrieve, grade_documents, generate, transform_query

def decide_to_generate(state: GraphState) -> str:
    if state.get("search_fallback"):
        return "transform_query"
    return "generate"

workflow = StateGraph(GraphState)

workflow.add_node("retrieve", retrieve)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("generate", generate)
workflow.add_node("transform_query", transform_query)

workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "grade_documents")
workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {
        "transform_query": "transform_query",
        "generate": "generate"
    }
)
workflow.add_edge("transform_query", "generate")
workflow.add_edge("generate", END)

app_graph = workflow.compile()