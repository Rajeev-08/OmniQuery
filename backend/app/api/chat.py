from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.graph.workflow import app_graph

router = APIRouter(prefix="/chat", tags=["Agentic Conversation"])

class ChatRequest(BaseModel):
    message: str

@router.post("")
async def conversational_agent_query(payload: ChatRequest):
    """
    Passes a user query into the self-corrective LangGraph workflow engine.
    Returns the final synthesized answer along with a full trace log of execution steps.
    """
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message body cannot be empty.")

    try:
        # Initialize the state map payload
        initial_state = {
            "question": payload.message,
            "generation": "",
            "search_fallback": False,
            "documents": [],
            "steps": []
        }
        
        # Invoke our compiled graph state machine synchronously
        final_output = app_graph.invoke(initial_state)
        
        return {
            "query": final_output["question"],
            "answer": final_output["generation"],
            "trace_timeline": final_output["steps"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during agent graph orchestration: {str(e)}"
        )