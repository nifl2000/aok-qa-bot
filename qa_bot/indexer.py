from __future__ import annotations

import json
import sqlite3

from sentence_transformers import SentenceTransformer

from qa_bot.models import MODEL_NAME


def _flatten_json(path: str) -> list[dict]:
    """Flatten hierarchical JSON into flat (frage, kanal) records."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    records = []
    for entry in data:
        hauptthema = entry["hauptthema"]
        for sub in entry.get("subthemen", []):
            subthema = sub["name"]
            for faq in sub.get("faqs", []):
                frage = faq["frage"]
                for antwort in faq.get("antworten", []):
                    records.append({
                        "hauptthema": hauptthema,
                        "subthema": subthema,
                        "frage": frage,
                        "kanal": antwort["kanal"],
                        "antwort": antwort["antwort"],
                    })
    return records


def build_index(
    json_path: str,
    db_path: str,
    model_name: str = MODEL_NAME,
) -> int:
    """Build embedding index from JSON data into SQLite.

    Returns number of indexed records.
    """
    records = _flatten_json(json_path)
    if not records:
        raise ValueError(f"No records found in {json_path}")

    print(f"Loading model {model_name}...")
    model = SentenceTransformer(model_name)

    print(f"Encoding {len(records)} records...")
    questions = [r["frage"] for r in records]
    embeddings = model.encode(questions, show_progress_bar=True)

    print(f"Writing to {db_path}...")
    db = sqlite3.connect(db_path)
    cur = db.cursor()

    cur.execute("DROP TABLE IF EXISTS faqs")
    cur.execute("DROP TABLE IF EXISTS faq_embeddings")

    cur.execute("""
        CREATE TABLE faqs (
            id INTEGER PRIMARY KEY,
            hauptthema TEXT NOT NULL,
            subthema TEXT NOT NULL,
            frage TEXT NOT NULL,
            kanal TEXT NOT NULL,
            antwort TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE faq_embeddings (
            faq_id INTEGER PRIMARY KEY,
            embedding BLOB NOT NULL,
            FOREIGN KEY (faq_id) REFERENCES faqs(id)
        )
    """)

    cur.executemany(
        "INSERT INTO faqs (hauptthema, subthema, frage, kanal, antwort) VALUES (?, ?, ?, ?, ?)",
        [(r["hauptthema"], r["subthema"], r["frage"], r["kanal"], r["antwort"]) for r in records],
    )

    cur.execute("SELECT id FROM faqs ORDER BY id")
    ids = [row[0] for row in cur.fetchall()]

    for faq_id, emb in zip(ids, embeddings):
        cur.execute(
            "INSERT INTO faq_embeddings (faq_id, embedding) VALUES (?, ?)",
            (faq_id, emb.tobytes()),
        )

    db.commit()
    db.close()

    print(f"Index built: {len(records)} records in {db_path}")
    return len(records)
