from __future__ import annotations

from dataclasses import dataclass, field

from qa_bot.config import (
    DEFAULT_DB_PATH,
    DEFAULT_JSON_PATH,
    DEFAULT_TOP_K,
    LLM_RERANK_BASE_URL,
    LLM_RERANK_MODEL,
    MODEL_NAME,
)



@dataclass
class Answer:
    kanal: str
    antwort: str


@dataclass
class FAQEntry:
    id: int
    hauptthema: str
    subthema: str
    frage: str
    answers: list[Answer] = field(default_factory=list)

    @property
    def kanal(self) -> str:
        """First available channel for backward compatibility."""
        return self.answers[0].kanal if self.answers else ""

    @property
    def antwort(self) -> str:
        """First available answer for backward compatibility."""
        return self.answers[0].antwort if self.answers else ""


@dataclass
class SearchResult:
    entry: FAQEntry
    score: float
    rrf_score: float = 0.0
    bm25_score: float = 0.0
    embed_score: float = 0.0
    rerank_score: float = 0.0
