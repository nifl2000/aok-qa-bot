"""Tests for qa_bot.retriever — search behavior."""

import sqlite3
import numpy as np
import pytest

from qa_bot.retriever import _sanitize_for_prompt


class TestSanitizeForPrompt:
    def test_removes_control_chars(self):
        result = _sanitize_for_prompt("hello\x00world")
        assert "\x00" not in result

    def test_truncates_long_input(self):
        long_text = "a " * 200
        result = _sanitize_for_prompt(long_text, max_len=50)
        assert len(result) <= 55

    def test_keeps_normal_text(self):
        assert _sanitize_for_prompt("Hello world") == "Hello world"


class TestBM25StopWords:
    """Verify BM25 stop words are applied."""

    def test_stop_words_filtered(self):
        from qa_bot.retriever import _BM25_STOP_WORDS
        # Common words should be excluded
        assert "und" in _BM25_STOP_WORDS
        assert "nicht" in _BM25_STOP_WORDS
        assert "werde" not in _BM25_STOP_WORDS  # not a stop word


class TestRRFMerge:
    def test_rrf_favors_consistent_winner(self):
        from qa_bot.retriever import Retriever
        # Doc 1 ranks first in both lists
        bm25 = [(1, 10.0), (2, 5.0), (3, 1.0)]
        embed = [(1, 0.9), (3, 0.5), (2, 0.3)]
        result = Retriever._rrf_merge(bm25, embed, top_k=3)
        assert list(result.keys())[0] == 1

    def test_rrf_returns_top_k(self):
        from qa_bot.retriever import Retriever
        bm25 = [(i, float(i)) for i in range(1, 20)]
        embed = [(i, 1.0 - i * 0.05) for i in range(1, 20)]
        result = Retriever._rrf_merge(bm25, embed, top_k=5)
        assert len(result) == 5
