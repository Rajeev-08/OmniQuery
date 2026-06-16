# OmniQuery

**OmniQuery** is an AI-powered Agentic Retrieval-Augmented Generation (RAG) platform that enables users to upload documents, create semantic knowledge bases, and interact with their data through intelligent conversational agents.

Built with **FastAPI**, **LangGraph**, **Google Gemini**, **PostgreSQL + pgvector**, and **React**, OmniQuery combines vector search, agentic reasoning, document retrieval, and web fallback mechanisms to deliver accurate and context-aware responses.

---

##  Features

###  Authentication & User Management

* Secure JWT-based authentication
* User registration and login
* Workspace-level document isolation
* Multi-user support

###  Document Intelligence

* Upload PDF and text-based documents
* Automatic text extraction
* Semantic chunking using Recursive Character Splitting
* Vector embedding generation with BAAI BGE models
* Storage in PostgreSQL with pgvector

###  Agentic RAG Workflow

* Built using LangGraph state machines
* Context retrieval from user documents
* LLM-based document relevance grading
* Automatic query transformation
* Web search fallback when internal knowledge is insufficient
* Explainable execution trace generation

###  Semantic Search

* Vector similarity search using pgvector
* Cosine similarity ranking
* High-performance retrieval pipeline

###  Conversational AI

* Persistent conversations
* Chat history storage
* Source tracking
* Context-aware responses

###  Web Fallback

* Automatic live web search when relevant information is unavailable in uploaded documents
* Self-correcting query optimization

---

##  Architecture

```text
                ┌─────────────────┐
                │   React Frontend │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ FastAPI Backend │
                └────────┬────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼

   Authentication   Document Upload   Chat API
       (JWT)         & Processing

                         │
                         ▼

                ┌─────────────────┐
                │ LangGraph Agent │
                └────────┬────────┘
                         │

        Retrieve → Grade → Generate
                         │
                         ▼

              Web Search Fallback

                         │
                         ▼

           PostgreSQL + pgvector
```

---

## 🛠️ Tech Stack

### Backend

* FastAPI
* LangGraph
* LangChain
* Google Gemini
* SQLAlchemy
* PostgreSQL
* pgvector

### AI & Machine Learning

* Sentence Transformers
* BAAI/bge-small-en-v1.5
* LangChain Embeddings
* Retrieval-Augmented Generation (RAG)

### Frontend

* React
* Vite
* Tailwind CSS

### Database

* PostgreSQL
* pgvector Extension

---

##  Project Structure

```bash
OmniQuery
│
├── backend
│   ├── app
│   │   ├── api
│   │   ├── core
│   │   ├── graph
│   │   ├── models
│   │   └── services
│   │
│   ├── main.py
│   └── requirements.txt
│
├── frontend
│   ├── src
│   ├── public
│   └── package.json
│
└── README.md
```

---

##  Installation

### 1. Clone Repository

```bash
git clone https://github.com/Rajeev-08/omniquery.git
cd omniquery
```

---

### 2. Backend Setup

Create a virtual environment:

```bash
python -m venv venv
```

Activate:

```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

### 3. PostgreSQL Setup

Install PostgreSQL and pgvector.

Create database:

```sql
CREATE DATABASE omniquery_db;
```

Enable extension:

```sql
CREATE EXTENSION vector;
```

---

### 4. Environment Variables

Create `.env`

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/omniquery_db

GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

---

### 5. Run Backend

```bash
uvicorn main:app --reload
```

Backend:

```text
http://localhost:8000
```

---

### 6. Run Frontend

```bash
cd frontend

npm install

npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

##  Agent Workflow

The conversational engine follows a self-corrective pipeline:

```text
User Query
     │
     ▼
Retrieve Documents
     │
     ▼
Grade Relevance
     │
     ├── Relevant ──► Generate Response
     │
     ▼
Not Relevant
     │
     ▼
Transform Query
     │
     ▼
Web Search
     │
     ▼
Generate Final Answer
```

---

##  API Endpoints

### Authentication

```http
POST /register
POST /login
```

### Documents

```http
POST   /upload
GET    /documents
DELETE /documents/{id}
```

### Conversations

```http
GET /conversations
GET /conversations/{id}/messages
```

### Chat

```http
POST /chat
```

---

## 🔮 Future Enhancements

* Multi-modal document support
* OCR pipeline
* Streaming responses
* Hybrid BM25 + Vector Retrieval
* Role-based access control
* Conversation memory optimization
* Multi-agent orchestration
* Kubernetes deployment

---

## 🤝 Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Open a Pull Request

---




