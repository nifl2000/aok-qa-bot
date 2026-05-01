"""Tests for qa_bot.indexer — _group_by_question function."""

import json
import os
import pytest

from qa_bot.indexer import _group_by_question, ensure_index


@pytest.fixture
def sample_json(tmp_path):
    """Create a minimal test JSON file."""
    data = [
        {
            "hauptthema": "Thema A",
            "subthemen": [
                {
                    "name": "Sub A1",
                    "faqs": [
                        {
                            "frage": "Frage 1?",
                            "antworten": [
                                {"kanal": "telefonisch", "antwort": "Antwort A1-1"},
                                {"kanal": "email", "antwort": "Antwort A1-2"},
                            ]
                        },
                        {
                            "frage": "Frage 2?",
                            "antworten": [
                                {"kanal": "telefonisch", "antwort": "Antwort A2-1"},
                            ]
                        },
                    ],
                },
            ],
        },
    ]
    path = tmp_path / "test.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_groups_by_question(sample_json):
    groups = _group_by_question(str(sample_json))
    assert len(groups) == 2
    assert groups[0]["frage"] == "Frage 1?"
    assert groups[1]["frage"] == "Frage 2?"


def test_preserves_first_subthema(sample_json):
    groups = _group_by_question(str(sample_json))
    assert groups[0]["subthema"] == "Sub A1"


def test_collects_all_answers(sample_json):
    groups = _group_by_question(str(sample_json))
    assert len(groups[0]["answers"]) == 2
    assert len(groups[1]["answers"]) == 1


def test_deduplicates_same_question_across_subthemen(tmp_path):
    """Same question in different subthemen should be merged."""
    data = [
        {
            "hauptthema": "Thema A",
            "subthemen": [
                {
                    "name": "Sub A1",
                    "faqs": [
                        {"frage": "Gleiche Frage?", "antworten": [{"kanal": "tel", "antwort": "Antwort 1"}]}
                    ],
                },
                {
                    "name": "Sub A2",
                    "faqs": [
                        {"frage": "Gleiche Frage?", "antworten": [{"kanal": "tel", "antwort": "Antwort 2"}]}
                    ],
                },
            ],
        },
    ]
    path = tmp_path / "dedup.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    groups = _group_by_question(str(path))
    assert len(groups) == 1
    assert len(groups[0]["answers"]) == 2


def test_deduplicates_exact_answer_within_group(tmp_path):
    """Exact same kanal+antwort should not be duplicated."""
    data = [
        {
            "hauptthema": "Thema A",
            "subthemen": [
                {
                    "name": "Sub A1",
                    "faqs": [
                        {
                            "frage": "Frage?",
                            "antworten": [
                                {"kanal": "tel", "antwort": "Identisch"},
                                {"kanal": "tel", "antwort": "Identisch"},
                            ]
                        }
                    ],
                },
            ],
        },
    ]
    path = tmp_path / "dup.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    groups = _group_by_question(str(path))
    assert len(groups[0]["answers"]) == 1


def test_empty_json(tmp_path):
    path = tmp_path / "empty.json"
    path.write_text("[]", encoding="utf-8")

    groups = _group_by_question(str(path))
    assert groups == []


class TestEnsureIndex:
    def test_does_nothing_if_db_exists(self, tmp_path):
        db_path = tmp_path / "existing.db"
        db_path.touch()
        # Should not raise even if json_path doesn't exist
        ensure_index(db_path=str(db_path), json_path="nonexistent.json")

    def test_raises_if_neither_db_nor_json(self, tmp_path):
        db_path = tmp_path / "missing.db"
        json_path = tmp_path / "missing.json"
        with pytest.raises(FileNotFoundError, match="source data"):
            ensure_index(db_path=str(db_path), json_path=str(json_path))
