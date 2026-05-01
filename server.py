#!/usr/bin/env python3
"""FastAPI server for the AOK Wissensportal QA-Bot."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from pydantic import BaseModel

from qa_bot.retriever import Retriever
from qa_bot.models import DEFAULT_TOP_K


class QueryRequest(BaseModel):
    question: str
    channel: str | None = None
    top_k: int = DEFAULT_TOP_K


retriever: Retriever | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global retriever
    retriever = Retriever()
    yield


app = FastAPI(title="AOK Wissensportal QA-Bot", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/query")
def query(
    q: str = Query(..., min_length=1, description="User's question"),
    channel: str | None = Query(None, description="Filter by channel"),
    top_k: int = Query(DEFAULT_TOP_K, ge=1, le=20, description="Number of results"),
):
    global retriever
    results = retriever.search(q, top_k=top_k, channel=channel)
    return {
        "query": q,
        "results": [
            {
                "score": r.score,
                "frage": r.entry.frage,
                "antwort": r.entry.antwort,
                "kanal": r.entry.kanal,
                "hauptthema": r.entry.hauptthema,
                "subthema": r.entry.subthema,
            }
            for r in results
        ],
    }


@app.post("/query")
def query_post(request: QueryRequest):
    global retriever
    results = retriever.search(request.question, top_k=request.top_k, channel=request.channel)
    return {
        "query": request.question,
        "results": [
            {
                "score": r.score,
                "frage": r.entry.frage,
                "antwort": r.entry.antwort,
                "kanal": r.entry.kanal,
                "hauptthema": r.entry.hauptthema,
                "subthema": r.entry.subthema,
            }
            for r in results
        ],
    }
