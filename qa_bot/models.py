from __future__ import annotations

from dataclasses import dataclass, field

MODEL_NAME = "intfloat/multilingual-e5-large"
DEFAULT_TOP_K = 5
DEFAULT_DB_PATH = "index.db"
DEFAULT_JSON_PATH = "input/Wissensportal_Hierarchisch_KOMPLETT_bereinigt.json"
LLM_RERANK_MODEL = "kimi-k2.5"
LLM_RERANK_BASE_URL = "https://coding-intl.dashscope.aliyuncs.com/v1"


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
