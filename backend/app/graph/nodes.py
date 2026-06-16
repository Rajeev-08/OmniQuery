import os
from pydantic import BaseModel, Field
from sqlalchemy import text
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.db import SessionLocal
from app.graph.state import GraphState
from app.services.embedding_service import embedding_engine
from langchain_community.tools import DuckDuckGoSearchRun

class GradeDocument(BaseModel):
    binary_score: str = Field(description="Document is relevant? Respond 'yes' or 'no'")

llm = ChatGoogleGenerativeAI(
    model="gemini-flash-latest", 
    google_api_key=os.getenv("GEMINI_API_KEY"), 
    temperature=0,
    max_retries=1  # Prevent infinite stalling if the 429 quota is completely maxed out
)

# Only bind if the library supports structured schema variants natively
try:
    structured_grader = llm.with_structured_output(GradeDocument)
except Exception:
    structured_grader = llm

web_search_tool = DuckDuckGoSearchRun()

def retrieve(state: GraphState) -> GraphState:
    print("--- [NODE EXECUTION]: SCALED NATIVE USER RETRIEVING ---")
    question = state["question"]
    user_id = state.get("user_id")
    
    if not user_id:
        return {**state, "documents": [], "steps": state.get("steps", []) + ["Missing authenticated user tracking context"]}

    query_vector = embedding_engine.generate_embeddings([question])[0]
    
    db = SessionLocal()
    try:
        sql_statement = text("""
            SELECT ud.file_name, dc.content 
            FROM document_chunks dc
            JOIN user_documents ud ON dc.document_id = ud.id
            WHERE ud.user_id = :user_id
            ORDER BY dc.embedding <=> CAST(:vector AS vector)
            LIMIT 4;
        """)
        results = db.execute(sql_statement, {"vector": str(query_vector), "user_id": user_id}).fetchall()
        documents = [{"file_name": r.file_name, "content": r.content} for r in results]
    finally:
        db.close()
        
    return {
        **state,
        "documents": documents,
        "steps": state.get("steps", []) + ["Internal Vector Retrieval Completed"]
    }

def grade_documents(state: GraphState) -> GraphState:
    print("--- [NODE EXECUTION]: GRADING ACCURACY OF CONTEXT ---")
    question = state["question"]
    documents = state["documents"]
    filtered_documents = []
    search_fallback = False

    if not documents:
        return {**state, "search_fallback": True, "steps": state.get("steps", []) + ["No workspace data found - Flagging search fallback"]}

    for doc in documents:
        system_prompt = (
            f"User Question: {question}\nContext Fragment: {doc['content']}\n\n"
            "Analyze if this snippet contains relevant facts to help answer. Respond with 'yes' or 'no'."
        )
        try:
            grade_result = structured_grader.invoke(system_prompt)
            # Handle standard dictionary or object unpacking variants gracefully
            score = getattr(grade_result, "binary_score", str(grade_result)).lower().strip()
            
            if "yes" in score:
                filtered_documents.append(doc)
            else:
                search_fallback = True
        except Exception as e:
            print(f"-> Quota/Grading Exception caught: {str(e)}. Falling back to token heuristics.")
            # RESILIENT FALLBACK: Simple string heuristic match if Gemini API rejects the request
            words = question.lower().split()
            match_count = sum(1 for word in words if len(word) > 3 and word in doc['content'].lower())
            if match_count > 0:
                filtered_documents.append(doc)
            else:
                search_fallback = True

    status = "Triggering Search Fallback" if search_fallback else "Context Verified Secure"
    return {**state, "documents": filtered_documents, "search_fallback": search_fallback, "steps": state.get("steps", []) + [f"Document Grading Completed: {status}"]}

def generate(state: GraphState) -> GraphState:
    print("--- [NODE EXECUTION]: SYNTHESIZING ANSWER VIA GEMINI ---")
    question = state["question"]
    documents = state["documents"]
    
    context_str = "\n\n".join([f"Source [{doc['file_name']}]: {doc['content']}" for doc in documents])
    system_prompt = f"Context:\n{context_str}\n\nQuestion: {question}\nAnswer clearly and comprehensively based on the context."
    
    try:
        response = llm.invoke(system_prompt)
        generation_text = response.content
    except Exception as e:
        print(f"-> Generation Quota Error caught: {str(e)}. Synthesizing via plain text context.")
        # RESILIENT FALLBACK: If final answer synthesis hits a 429, spit back the pure extracted text context directly to the user
        if documents:
            generation_text = f"[API Quota Exceeded - Displaying Extracted Context Directly]:\n\n" + "\n\n".join([d['content'] for d in documents])
        else:
            generation_text = "The Gemini API quota limits have been exceeded for today, and no reliable text context could be extracted from local caches."

    return {**state, "generation": generation_text, "steps": state.get("steps", []) + ["Final Synthesis Layer Executed"]}

def transform_query(state: GraphState) -> GraphState:
    print("--- [NODE EXECUTION]: RUNNING SELF-CORRECTIVE WEB FALLBACK ---")
    question = state["question"]
    documents = state.get("documents", [])
    system_prompt = f"Rewrite this search query to optimize for web results: {question}. Respond with ONLY the query phrase."

    try:
        optimized_query = llm.invoke(system_prompt).content.strip().replace('"', '')
    except Exception:
        # RESILIENT FALLBACK: Use original question directly if query optimizer throws 429
        optimized_query = question

    try:
        print(f"-> Executing DuckDuckGo lookup for: '{optimized_query}'")
        search_results = web_search_tool.run(optimized_query)
        web_document = {"file_name": "Live Web Search Fallback Engine", "content": search_results}
        updated_docs = documents + [web_document]
    except Exception as e:
        print(f"Web lookup tool failure: {str(e)}")
        updated_docs = documents

    return {**state, "documents": updated_docs, "steps": state.get("steps", []) + [f"Web Fallback Query Executed"]}