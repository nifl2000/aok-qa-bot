import logging
import os
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Ensure the project root (parent of backend/) is on the import path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from qa_bot.indexer import ensure_index
from qa_bot.retriever import Retriever
from qa_bot.config import llm_api_key
from qa_bot.text_utils import clean_answer

# ── Configuration ────────────────────────────────────────────────────────

API_PASSWORD = os.environ.get("AOK_BOT_PASSWORD", "aok2026")
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
MAX_QUERY_LENGTH = 500

# ── Logging ──────────────────────────────────────────────────────────────

class _RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = getattr(record, "request_id", "—")
        return True


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(request_id)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("aok-qa-bot")
for handler in logging.root.handlers:
    handler.addFilter(_RequestIdFilter())


# ── Lifespan ─────────────────────────────────────────────────────────────

_retriever: Optional[Retriever] = None
_startup_error: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _retriever, _startup_error
    logger.info("Backend starting up...")

    if not llm_api_key():
        logger.warning("LLM_API_KEY not configured")

    try:
        ensure_index()
    except Exception as e:
        _startup_error = f"Could not ensure index: {e}"
        logger.error(_startup_error)
        yield
        return

    try:
        logger.info("Loading embedding models...")
        _retriever = Retriever()
        logger.info("Backend ready. Indexed entries: %d", len(_retriever.entries))
    except Exception as e:
        _startup_error = f"Failed to load retriever: {e}"
        logger.error(_startup_error)

    yield

    logger.info("Shutting down")
    _retriever = None


app = FastAPI(title="AOK QA-Bot API", version="1.0.0", lifespan=lifespan)

# ── Middleware ───────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    # Inject request_id into logger for this coroutine
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.request_id = request_id
        return record

    logging.setLogRecordFactory(record_factory)
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        logging.setLogRecordFactory(old_factory)


# ── Data Models ──────────────────────────────────────────────────────────

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


class SearchResponse(BaseModel):
    query: str
    results: List[FAQResult]


# ── Endpoints ────────────────────────────────────────────────────────────

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "version": app.version}


@app.get("/api/ready")
def readiness_check():
    global _retriever, _startup_error
    if _startup_error:
        raise HTTPException(status_code=503, detail=_startup_error)
    if _retriever is None:
        raise HTTPException(status_code=503, detail="Retriever not loaded")
    return {"status": "ready", "entries": len(_retriever.entries)}


@app.post("/api/v1/search", response_model=SearchResponse)
async def search(request: SearchRequest, x_password: str = Header(default=None, alias="X-Password")):
    if x_password != API_PASSWORD:
        raise HTTPException(status_code=401, detail="Unauthorized")

    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    if len(query) > MAX_QUERY_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Query too long (max {MAX_QUERY_LENGTH} characters)."
        )

    global _retriever
    if _retriever is None:
        raise HTTPException(status_code=503, detail="Search engine not ready")

    try:
        raw_results = _retriever.search(
            query=query,
            top_k=request.top_k,
            topic=request.topic,
        )

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
            ))

        logger.info("Search query='%s' results=%d", query[:80], len(results))
        return SearchResponse(query=query, results=results)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Search failed for query='%s': %s", query[:80], e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "request_id": getattr(request.state, "request_id", "")},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "request_id": getattr(request.state, "request_id", ""),
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
