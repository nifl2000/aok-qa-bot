"""Tests for the FastAPI backend endpoints."""

import os
import sys

import pytest
from fastapi.testclient import TestClient

# Ensure the project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def client(tmp_path):
    """Create a test client with an empty index."""
    import sqlite3
    import numpy as np

    # Create a minimal test index
    db_path = str(tmp_path / "test.db")
    db = sqlite3.connect(db_path)
    cur = db.cursor()
    cur.execute("""
        CREATE TABLE faqs (
            id INTEGER PRIMARY KEY, frage TEXT, hauptthema TEXT,
            subthema TEXT, answers_json TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE faq_embeddings (faq_id INTEGER PRIMARY KEY, embedding BLOB)
    """)
    cur.execute("""
        CREATE VIRTUAL TABLE faqs_fts USING fts5(frage, hauptthema, content='faqs', content_rowid='id')
    """)

    cur.execute(
        "INSERT INTO faqs (id, frage, hauptthema, subthema, answers_json) VALUES (?, ?, ?, ?, ?)",
        (1, "Was ist ein Freischaltcode?", "Digitale Gesundheitsanwendungen", "Sub", '[]'),
    )
    cur.execute(
        "INSERT INTO faq_embeddings (faq_id, embedding) VALUES (?, ?)",
        (1, np.zeros(10, dtype=np.float32).tobytes()),
    )
    cur.execute(
        "INSERT INTO faqs_fts (rowid, frage, hauptthema) VALUES (?, ?, ?)",
        (1, "Was ist ein Freischaltcode?", "Digitale Gesundheitsanwendungen"),
    )
    db.commit()
    db.close()

    monkeypatch_env = pytest.MonkeyPatch()
    monkeypatch_env.setenv("AOK_BOT_PASSWORD", "testpw")
    monkeypatch_env.setenv("LLM_API_KEY", "dummy")

    # We import here so env vars are set
    from backend.main import app, API_PASSWORD
    app.dependency_overrides = {}

    yield TestClient(app)

    monkeypatch_env.undo()


class TestAuth:
    def test_search_without_password(self, client):
        resp = client.post("/api/v1/search", json={"query": "test"})
        assert resp.status_code == 401

    def test_search_wrong_password(self, client):
        resp = client.post(
            "/api/v1/search",
            json={"query": "test"},
            headers={"X-Password": "wrong"},
        )
        assert resp.status_code == 401

    def test_search_correct_password(self, client):
        resp = client.post(
            "/api/v1/search",
            json={"query": "test"},
            headers={"X-Password": "testpw"},
        )
        # 503 expected because retriever is not loaded in test
        assert resp.status_code in (200, 503)


class TestHealth:
    def test_health_returns_200(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "version" in data


class TestValidation:
    def test_search_empty_query_rejected(self, client):
        resp = client.post(
            "/api/v1/search",
            json={"query": "   "},
            headers={"X-Password": "testpw"},
        )
        assert resp.status_code == 400

    def test_search_overlong_query_rejected(self, client):
        resp = client.post(
            "/api/v1/search",
            json={"query": "x" * 600},
            headers={"X-Password": "testpw"},
        )
        assert resp.status_code == 400
