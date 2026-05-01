import os
import sys
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure the root directory is in sys.path so we can import qa_bot
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qa_bot.retriever import Retriever
from qa_bot.indexer import ensure_index
from qa_bot.config import llm_api_key
from qa_bot.text_utils import clean_answer

app = FastAPI(title="AOK QA-Bot API", version="1.0.0")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Data Models ---

class SearchRequest(BaseModel):
    query: str
    top_k: int = 3
    topic: Optional[str] = None

class Answer(BaseModel):
    kanal: str
    antwort: str

class FAQResult(BaseModel):
    id: int
    frage: str
    hauptthema: str
    subthema: str
    answers: List[Answer]
    score: float

class SearchResponse(BaseModel):
    query: str
    results: List[FAQResult]

# --- State ---

# Global retriever instance
retriever: Optional[Retriever] = None

@app.on_event("startup")
def startup_event():
    global retriever
    print("Backend starting up...")
    
    # 1. Ensure API Key exists
    if not llm_api_key():
        print("CRITICAL: LLM_API_KEY not found in environment or .env file.")
    
    # 2. Ensure Index exists
    try:
        ensure_index()
    except Exception as e:
        print(f"CRITICAL: Could not ensure index: {e}")
        return

    # 3. Initialize Retriever
    print("Loading models (this might take a moment)...")
    retriever = Retriever()
    print("Backend ready.")

# --- Endpoints ---

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy", 
        "retriever_loaded": retriever is not None,
        "llm_key_configured": llm_api_key() is not None
    }

@app.post("/api/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    if retriever is None:
        raise HTTPException(status_code=503, detail="Search engine is still loading or failed to initialize.")
    
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        # We use the new defaults: llm_rerank=True
        raw_results = retriever.search(
            query=request.query,
            top_k=request.top_k,
            topic=request.topic
        )
        
        # Convert to response models
        results = []
        for res in raw_results:
            results.append(FAQResult(
                id=res.entry.id,
                frage=res.entry.frage,
                hauptthema=res.entry.hauptthema,
                subthema=res.entry.subthema,
                answers=[
                    Answer(kanal=a.kanal, antwort=clean_answer(a.antwort)) 
                    for a in res.entry.answers
                ],
                score=res.score
            ))
            
        return SearchResponse(query=request.query, results=results)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
