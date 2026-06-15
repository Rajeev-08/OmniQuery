import os
from pydantic import BaseModel, Field
from sqlalchemy import text
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.db import SessionLocal
from app.graph.state import GraphState
from app.services.embedding_service import embedding_engine
from langchain_community.tools import DuckDuckGoSearchRun

class GradeDocument(BaseModel):
    binary_score: str = Field(
        description="Document is relevant to the question? Respond strictly with 'yes' or 'no'"
    )

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0
)

structured_grader = llm.with_structured_output(GradeDocument)
web_search_tool = DuckDuckGoSearchRun()

def retrieve(state: GraphState) -> GraphState:
    print("--- [NODE EXECUTION]: RETRIEVING FROM PGVECTOR ---")
    question = state["question"]
    
    query_vector = embedding_engine.generate_embeddings([question])[0]
    
    db = SessionLocal()
    try:
        sql_statement = text("""
            SELECT file_name, content 
            FROM document_chunks
            ORDER BY embedding <=> CAST(:vector AS vector)
            LIMIT 4;
        """)
        results = db.execute(sql_statement, {"vector": str(query_vector)}).fetchall()
        
        documents = [{"file_name": r.file_name, "content": r.content} for r in results]
    finally:
        db.close()
        
    print(f"-> Successfully retrieved {len(documents)} context fragments.")
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
    log_steps = []

    if not documents:
        print("-> Warning: Vector database returned zero context blocks. Directing to fallback.")
        return {**state, "search_fallback": True, "steps": state.get("steps", []) + ["No database data found - Flagging search fallback"]}

    for doc in documents:
        system_prompt = (
            "You are a strict QA grader analyzing whether a retrieved document snippet contains "
            "relevant facts to help answer a user's question.\n"
            f"User Question: {question}\n"
            f"Retrieved Document Context: {doc['content']}\n\n"
            "Analyze carefully. If the document references terms, synonyms, or background facts linked directly "
            "to the user question, grade it as 'yes'. Otherwise, grade it as 'no'."
        )
        
        try:
            grade_result = structured_grader.invoke(system_prompt)
            score = grade_result.binary_score.lower().strip()
            
            if score == "yes":
                print(f"-> [GRADE: RELEVANT] Fragment matching source: {doc['file_name']}")
                filtered_documents.append(doc)
            else:
                print(f"-> [GRADE: IRRELEVANT] Filtering out chunk from source: {doc['file_name']}")
                search_fallback = True
        except Exception as e:
            print(f"Grading exception encountered: {str(e)}. Defaulting chunk to fallback processing.")
            search_fallback = True

    status_summary = "Triggering Search Fallback" if search_fallback else "Context Verified Secure"
    log_steps.append(f"Document Grading Completed: {status_summary}")

    return {
        **state,
        "documents": filtered_documents,
        "search_fallback": search_fallback,
        "steps": state.get("steps", []) + log_steps
    }

def generate(state: GraphState) -> GraphState:
    print("--- [NODE EXECUTION]: SYNTHESIZING ANSWER VIA GEMINI ---")
    question = state["question"]
    documents = state["documents"]
    
    context_str = "\n\n".join([f"Source [{doc['file_name']}]: {doc['content']}" for doc in documents])
    
    system_prompt = (
        "You are an elite enterprise knowledge assistant answering technical questions.\n"
        "Use the provided context blocks to form a crisp, comprehensive, and accurate response.\n"
        "If you do not know the answer or if the context is insufficient, state that clearly.\n"
        "Always keep your tone professional and grounded in the retrieved facts.\n\n"
        f"Retrieved Context:\n{context_str}\n\n"
        f"User Question: {question}"
    )
    
    try:
        response = llm.invoke(system_prompt)
        generation_text = response.content
    except Exception as e:
        generation_text = f"Failed to synthesize response due to an internal LLM error: {str(e)}"

    return {
        **state,
        "generation": generation_text,
        "steps": state.get("steps", []) + ["Final Synthesis Layer Executed Successfully"]
    }

def transform_query(state: GraphState) -> GraphState:
    print("--- [NODE EXECUTION]: RUNNING SELF-CORRECTIVE WEB FALLBACK ---")
    question = state["question"]
    documents = state.get("documents", [])

    system_prompt = (
        "You are a search query optimizer. The user asked a question, but our internal data "
        "stores did not return relevant documentation. Your job is to rewrite this query to maximize "
        "the relevance of web search results.\n"
        "Respond with ONLY the optimized search phrase. Do not include markdown, quotes, or prefaces.\n\n"
        f"Original Question: {question}"
    )

    try:
        optimized_query_response = llm.invoke(system_prompt)
        optimized_query = optimized_query_response.content.strip().replace('"', '')
        print(f"-> Original Query: '{question}' | Optimized To: '{optimized_query}'")
        
        search_results = web_search_tool.run(optimized_query)
        
        web_document = {
            "file_name": "Live Web Search Fallback Engine",
            "content": search_results
        }
        updated_docs = documents + [web_document]
        
    except Exception as e:
        print(f"Web fallback execution encountered an error: {str(e)}")
        updated_docs = documents

    return {
        **state,
        "documents": updated_docs,
        "steps": state.get("steps", []) + [f"Web Fallback Query Created: '{optimized_query}'"]
    }