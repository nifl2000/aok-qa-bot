"""Tests for qa_bot.config."""

import os

from qa_bot import config


class TestDefaults:
    def test_model_name(self):
        assert config.MODEL_NAME == "intfloat/multilingual-e5-large"

    def test_db_path(self):
        assert config.DEFAULT_DB_PATH == "index.db"

    def test_llm_model(self):
        assert config.LLM_RERANK_MODEL == "kimi-k2.5"

    def test_llm_base_url(self):
        assert config.LLM_RERANK_BASE_URL == "https://coding-intl.dashscope.aliyuncs.com/v1"

    def test_default_top_k(self):
        assert config.DEFAULT_TOP_K == 5

    def test_default_llm_rerank_top_k(self):
        assert config.DEFAULT_LLM_RERANK_TOP_K == 20


class TestLlmApiKey:
    def test_returns_key_when_set(self, monkeypatch):
        monkeypatch.setenv("LLM_API_KEY", "test-key-123")
        assert config.llm_api_key() == "test-key-123"

    def test_returns_none_when_not_set(self, monkeypatch):
        monkeypatch.delenv("LLM_API_KEY", raising=False)
        assert config.llm_api_key() is None
