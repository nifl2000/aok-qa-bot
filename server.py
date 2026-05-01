#!/usr/bin/env python3
"""FastAPI server for the AOK Wissensportal QA-Bot."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from qa_bot.retriever import Retriever
from qa_bot.models import DEFAULT_TOP_K


class QueryRequest(BaseModel):
    question: str
    channel: str | None = None
    top_k: int = DEFAULT_TOP_K


class ResultItem(BaseModel):
    score: float
    frage: str
    antwort: str
    kanal: str
    hauptthema: str
    subthema: str


class QueryResponse(BaseModel):
    query: str
    results: list[ResultItem]


retriever: Retriever | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global retriever
    retriever = Retriever()
    yield


app = FastAPI(title="AOK Wissensportal QA-Bot", lifespan=lifespan)


def _format_results(query: str, results) -> QueryResponse:
    return QueryResponse(
        query=query,
        results=[
            ResultItem(
                score=r.score,
                frage=r.entry.frage,
                antwort=r.entry.antwort,
                kanal=r.entry.kanal,
                hauptthema=r.entry.hauptthema,
                subthema=r.entry.subthema,
            )
            for r in results
        ],
    )


def _ensure_retriever() -> Retriever:
    if retriever is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    return retriever


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/query", response_model=QueryResponse)
def query(
    q: str = Query(..., min_length=1, description="User's question"),
    channel: str | None = Query(None, description="Filter by channel"),
    top_k: int = Query(DEFAULT_TOP_K, ge=1, le=20, description="Number of results"),
) -> QueryResponse:
    r = _ensure_retriever()
    try:
        results = r.search(q, top_k=top_k, channel=channel)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return _format_results(q, results)


@app.post("/query", response_model=QueryResponse)
def query_post(request: QueryRequest) -> QueryResponse:
    r = _ensure_retriever()
    try:
        results = r.search(request.question, top_k=request.top_k, channel=request.channel)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return _format_results(request.question, results)
