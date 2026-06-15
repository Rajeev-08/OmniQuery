from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.db import init_db
from app.api import upload, retrieval, chat  # Import the new chat router

app = FastAPI(title="OmniQuery AI Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    print("Initializing OmniQuery Database and Extensions...")
    init_db()
    print("Database configured successfully!")

# Mount API endpoints
app.include_router(upload.router)
app.include_router(retrieval.router)
app.include_router(chat.router)  # Live Chat Agent Node

@app.get("/")
def health_check():
    return {"status": "online", "engine": "OmniQuery RAG Platform"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)