import os
import hashlib
import jwt
import datetime
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import io
from pypdf import PdfReader


from app.core.db import init_db, get_db
from app.models.vector_store import User, UserDocument, Conversation, Message
from app.services.vector_service import vector_service
from app.graph.workflow import app_graph

SECRET_KEY = "omniquery_super_secure_secret_key_change_in_production"
ALGORITHM = "HS256"

app = FastAPI(title="OmniQuery Corporate Workspace Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

# --- Security & Token Processing Utilities ---
class AuthRequest(BaseModel):
    username: str
    password: str

def get_password_hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return get_password_hash(plain_password) == hashed_password

def get_current_user_id(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> int:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authentication credentials.")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token payload signatures.")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Session expired or token is corrupt.")
        
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User target space no longer exists.")
    return user.id

def get_current_username(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        return "Anonymous User"
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub", "Anonymous User")
    except Exception:
        return "Anonymous User"

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None

# --- Authentic Identity Gateways ---
@app.post("/register")
def register_account(payload: AuthRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == payload.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username is already taken.")
    
    hashed_pwd = get_password_hash(payload.password)
    new_user = User(username=payload.username, hashed_password=hashed_pwd)
    db.add(new_user)
    db.commit()
    return {"status": "success", "message": "Account registered successfully. Proceed to login."}

@app.post("/login")
def login_session(payload: AuthRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password entry.")
        
    expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    token_data = {"sub": user.username, "exp": expiration}
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user.username
    }

# --- Document Route Blueprints ---
@app.post("/upload")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    file_name = file.filename.lower()
    raw_text = ""

    try:
        contents = await file.read()
        
        # 1. Condition: Handle PDF Binary Extraction
        if file_name.endswith(".pdf"):
            pdf_stream = io.BytesIO(contents)
            pdf_reader = PdfReader(pdf_stream)
            extracted_pages = []
            
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    extracted_pages.append(page_text)
            
            raw_text = "\n\n".join(extracted_pages)
            
        # 2. Condition: Handle Standard Flat Text Formats (.txt, .md, .json)
        else:
            raw_text = contents.decode("utf-8")
            
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Failed to parse document stream. Error: {str(e)}"
        )

    if not raw_text.strip():
        raise HTTPException(
            status_code=400, 
            detail="The system was unable to extract any readable text context from this file."
        )

    # Hand off the clean string to our database vector engine
    total_chunks = vector_service.ingest_document(
        db=db, 
        user_id=user_id, 
        file_name=file.filename, 
        file_type=file.content_type, 
        raw_text=raw_text
    )
    
    return {"status": "success", "file_name": file.filename, "chunks_ingested": total_chunks}
@app.get("/documents")
def list_documents(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    docs = db.query(UserDocument).filter(UserDocument.user_id == user_id).all()
    return [{"id": d.id, "file_name": d.file_name, "created_at": d.created_at} for d in docs]

@app.delete("/documents/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    doc = db.query(UserDocument).filter(UserDocument.id == document_id, UserDocument.user_id == user_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    db.delete(doc)
    db.commit()
    return {"status": "success", "message": "Document and all embedded vectors removed atomically."}

# --- Multi-User Conversation State Routes ---
@app.get("/conversations")
def list_conversations(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    convs = db.query(Conversation).filter(Conversation.user_id == user_id).order_by(Conversation.created_at.desc()).all()
    return [{"id": c.id, "title": c.title, "created_at": c.created_at} for c in convs]

@app.get("/conversations/{conversation_id}/messages")
def get_chat_history(conversation_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == user_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Chat session records unavailable.")
    return [{
        "role": m.role,
        "content": m.content,
        "trace_timeline": m.trace_timeline,
        "sources": m.sources
    } for m in conv.messages]

@app.post("/chat")
async def conversational_agent_query(payload: ChatRequest, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id), username: str = Depends(get_current_username)):
    conv_id = payload.conversation_id
    if not conv_id:
        new_conv = Conversation(user_id=user_id, title=payload.message[:30] + "...")
        db.add(new_conv)
        db.commit()
        db.refresh(new_conv)
        conv_id = new_conv.id

    initial_state = {
        "user_id": user_id,
        "question": payload.message,
        "generation": "",
        "search_fallback": False,
        "documents": [],
        "steps": []
    }
    
    final_output = app_graph.invoke(initial_state)
    sources = list(set([doc["file_name"] for doc in final_output.get("documents", [])]))

    user_msg = Message(conversation_id=conv_id, role=username, content=payload.message)
    assistant_msg = Message(
        conversation_id=conv_id, 
        role="OmniQuery Agent", 
        content=final_output["generation"],
        trace_timeline=final_output["steps"],
        sources=sources
    )
    db.add(user_msg)
    db.add(assistant_msg)
    db.commit()

    return {
        "conversation_id": conv_id,
        "answer": final_output["generation"],
        "trace_timeline": final_output["steps"],
        "sources": sources
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)