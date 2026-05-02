"""Tests for qa_bot.topic_filter."""

import pytest
from qa_bot.topic_filter import _extract_words, TopicFilter


class TestExtractWords:
    def test_removes_stop_words(self):
        assert "und" not in _extract_words("was ist und wie")

    def test_keeps_content_words(self):
        words = _extract_words("Freischaltcode Digitale")
        assert "freischaltcode" in words
        assert "digitale" in words

    def test_ignores_short_words(self):
        assert "is" not in _extract_words("is der ein")

    def test_handles_umlauts(self):
        # Compound word stays as single token
        words = _extract_words("Müttervorsorge")
        assert len(words) == 1
        assert "mütter" in words[0]


class TestTopicFilterNormalize:
    def test_replaces_umlauts(self):
        assert TopicFilter.normalize_topic("Mütterschutz") == "Muetterschutz"
        assert TopicFilter.normalize_topic("für") == "fuer"

    def test_replaces_eszett(self):
        assert TopicFilter.normalize_topic("Große") == "Grosse"
