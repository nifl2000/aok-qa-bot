from __future__ import annotations

import os


# ── Defaults ──────────────────────────────────────────────────────────────

MODEL_NAME = "intfloat/multilingual-e5-large"
DEFAULT_DB_PATH = "index.db"
DEFAULT_JSON_PATH = "input/Wissensportal_Hierarchisch_KOMPLETT_bereinigt.json"
LLM_RERANK_MODEL = "kimi-k2.5"
LLM_RERANK_BASE_URL = "https://coding-intl.dashscope.aliyuncs.com/v1"
DEFAULT_TOP_K = 5
DEFAULT_LLM_RERANK_TOP_K = 20


# ── Env helpers ───────────────────────────────────────────────────────────

def llm_api_key() -> str | None:
    """Load LLM API key from environment."""
    return os.environ.get("LLM_API_KEY")
