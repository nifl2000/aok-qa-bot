from __future__ import annotations

import json
import os
import sqlite3
from collections import OrderedDict

from sentence_transformers import SentenceTransformer

from qa_bot.config import DEFAULT_DB_PATH, DEFAULT_JSON_PATH
from qa_bot.models import MODEL_NAME


def _group_by_question(path: str) -> list[dict]:
    """Flatten and group JSON by (frage, hauptthema).

    Returns a list of deduplicated FAQ entries, each with:
    - frage, hauptthema, subthema (first occurrence)
    - answers: list of {kanal, antwort} dicts
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    # Use OrderedDict to preserve insertion order while grouping
    groups: OrderedDict[tuple[str, str], dict] = OrderedDict()

    for entry in data:
        hauptthema = entry["hauptthema"]
        for sub in entry.get("subthemen", []):
            subthema = sub["name"]
            for faq in sub.get("faqs", []):
                frage = faq["frage"]
                key = (frage, hauptthema)
                if key not in groups:
                    groups[key] = {
                        "frage": frage,
                        "hauptthema": hauptthema,
                        "subthema": subthema,
                        "answers": [],
                    }
                for antwort in faq.get("antworten", []):
                    # Avoid exact duplicate answers within the same group
                    answer_entry = {
                        "kanal": antwort["kanal"],
                        "antwort": antwort["antwort"],
                    }
                    if answer_entry not in groups[key]["answers"]:
                        groups[key]["answers"].append(answer_entry)

    return list(groups.values())


def build_index(
    json_path: str,
    db_path: str,
    model_name: str = MODEL_NAME,
) -> int:
    """Build deduplicated embedding + FTS5 index from JSON data into SQLite.

    Returns number of indexed (deduplicated) FAQ entries.
    """
    groups = _group_by_question(json_path)
    if not groups:
        raise ValueError(f"No records found in {json_path}")

    print(f"Loading model {model_name}...")
    model = SentenceTransformer(model_name)

    print(f"Encoding {len(groups)} deduplicated entries...")
    # Include category in embedding for better context
    texts_to_encode = [f"{g['hauptthema']}: {g['frage']}" for g in groups]
    embeddings = model.encode(texts_to_encode, show_progress_bar=True)

    print(f"Writing to {db_path}...")
    db = sqlite3.connect(db_path)
    cur = db.cursor()

    # Drop old tables
    cur.execute("DROP TABLE IF EXISTS faqs")
    cur.execute("DROP TABLE IF EXISTS faq_embeddings")
    cur.execute("DROP TABLE IF EXISTS faqs_fts")

    # Create deduped FAQ table
    cur.execute("""
        CREATE TABLE faqs (
            id INTEGER PRIMARY KEY,
            frage TEXT NOT NULL,
            hauptthema TEXT NOT NULL,
            subthema TEXT NOT NULL,
            answers_json TEXT NOT NULL
        )
    """)

    # Create embedding table
    cur.execute("""
        CREATE TABLE faq_embeddings (
            faq_id INTEGER PRIMARY KEY,
            embedding BLOB NOT NULL,
            FOREIGN KEY (faq_id) REFERENCES faqs(id)
        )
    """)

    # Create FTS5 virtual table for BM25/hybrid search
    cur.execute("""
        CREATE VIRTUAL TABLE faqs_fts USING fts5(
            frage, hauptthema,
            content='faqs', content_rowid='id'
        )
    """)

    # Insert grouped entries
    for i, g in enumerate(groups):
        answers_json = json.dumps(g["answers"], ensure_ascii=False)
        cur.execute(
            "INSERT INTO faqs (frage, hauptthema, subthema, answers_json) VALUES (?, ?, ?, ?)",
            (g["frage"], g["hauptthema"], g["subthema"], answers_json),
        )
        faq_id = cur.lastrowid

        # Insert embedding
        cur.execute(
            "INSERT INTO faq_embeddings (faq_id, embedding) VALUES (?, ?)",
            (faq_id, embeddings[i].tobytes()),
        )

        # Populate FTS5 index
        cur.execute(
            "INSERT INTO faqs_fts(rowid, frage, hauptthema) VALUES (?, ?, ?)",
            (faq_id, g["frage"], g["hauptthema"]),
        )

    db.commit()
    db.close()

    print(f"Index built: {len(groups)} deduplicated entries in {db_path}")
    return len(groups)


def ensure_index(db_path: str = DEFAULT_DB_PATH, json_path: str = DEFAULT_JSON_PATH) -> None:
    """Build index from JSON if it doesn't exist yet.

    Silent if index already exists.
    """
    if os.path.exists(db_path):
        return
    if not os.path.exists(json_path):
        raise FileNotFoundError(
            f"Index file '{db_path}' not found and source data '{json_path}' missing. "
            "Please run: python build_index.py"
        )
    build_index(json_path, db_path)
