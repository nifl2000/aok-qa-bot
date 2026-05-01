from __future__ import annotations

from dataclasses import dataclass

MODEL_NAME = "intfloat/multilingual-e5-large"
DEFAULT_TOP_K = 5
DEFAULT_DB_PATH = "index.db"
DEFAULT_JSON_PATH = "input/Wissensportal_Hierarchisch_KOMPLETT_bereinigt.json"


@dataclass
class FAQEntry:
    id: int
    hauptthema: str
    subthema: str
    frage: str
    kanal: str
    antwort: str


@dataclass
class SearchResult:
    entry: FAQEntry
    score: float
