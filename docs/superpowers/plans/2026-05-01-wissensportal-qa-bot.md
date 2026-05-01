# Wissensportal QA-Bot MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Lokaler QA-Bot der AOK-Wissensportal-Daten (1400 FAQs, 4992 kanalisierte Antworten) mit semantischer Embedding-Suche.

**Architecture:** Einmaliger Index-Build (JSON → Embeddings → SQLite), dann schnelle Retrieval-Queries (~10ms) via Cosine Similarity. CLI + FastAPI Server als Interfaces.

**Tech Stack:** Python 3.11+, sentence-transformers (multilingual-e5-large), numpy, sqlite3, fastapi

---

## File Map

| File | Responsibility |
|---|---|
| `requirements.txt` | Dependencies |
| `qa_bot/__init__.py` | Package init, exports |
| `qa_bot/models.py` | Shared data classes and constants |
| `qa_bot/indexer.py` | JSON parsen, Embeddings berechnen, SQLite befüllen |
| `qa_bot/retriever.py` | Query embedden, Cosine Similarity, Top-K zurückgeben |
| `build_index.py` | Einmal-Skript: `python build_index.py` |
| `cli.py` | Terminal-Interface: `python cli.py "Frage?"` |
| `server.py` | FastAPI Server mit `/query` Endpoint |

## Data Model

Jeder (Frage, Kanal)-Kombination ist ein separater Such-Eintrag. Dieselbe Frage kann verschiedene Antworten je Kanal haben.

```python
@dataclass
class FAQEntry:
    id: int              # SQLite row id
    hauptthema: str      # z.B. "Mutterschaftsgeld"
    subthema: str        # z.B. "Allgemein / Sonstiges"
    frage: str           # z.B. "Wann beginnt und endet der Mutterschutz?"
    kanal: str           # z.B. "telefonisch"
    antwort: str         # Antworttext
```

---

### Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `qa_bot/__init__.py`
- Create: `qa_bot/models.py`

- [ ] **Step 1: Create requirements.txt**

```txt
sentence-transformers>=3.0.0
numpy>=1.26.0
fastapi[standard]>=0.115.0
```

- [ ] **Step 2: Create qa_bot/__init__.py**

```python
from qa_bot.models import FAQEntry
from qa_bot.indexer import build_index
from qa_bot.retriever import Retriever

__all__ = ["FAQEntry", "build_index", "Retriever"]
```

- [ ] **Step 3: Create qa_bot/models.py**

```python
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
```

- [ ] **Step 4: Verify package imports**

Run: `python -c "from qa_bot.models import FAQEntry, SearchResult; print('OK')"`
Expected: `OK`

- [ ] **Step 5: Install dependencies**

Run: `pip install -r requirements.txt`
Expected: All packages installed without errors

- [ ] **Step 6: Commit**

```bash
git add requirements.txt qa_bot/__init__.py qa_bot/models.py
git commit -m "feat: project setup with data models"
```

---

### Task 2: Indexer

**Files:**
- Create: `qa_bot/indexer.py`
- Create: `build_index.py`

- [ ] **Step 1: Write indexer core logic**

Create `qa_bot/indexer.py`:

```python
from __future__ import annotations

import json
import sqlite3

import numpy as np
from sentence_transformers import SentenceTransformer

from qa_bot.models import FAQEntry, MODEL_NAME


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

    # Get the IDs we just inserted
    cur.execute("SELECT id FROM faqs ORDER BY id")
    ids = [row[0] for row in cur.fetchall()]

    for faq_id, emb in zip(ids, embeddings):
        cur.execute(
            "INSERT INTO faq_embeddings (faq_id, embedding) VALUES (?, ?)",
            (faq_id, np.array(emb).tobytes()),
        )

    db.commit()
    db.close()

    print(f"Index built: {len(records)} records in {db_path}")
    return len(records)
```

- [ ] **Step 2: Create build_index.py entry point**

```python
#!/usr/bin/env python3
"""Build the FAQ embedding index. Usage: python build_index.py"""

from qa_bot.indexer import build_index
from qa_bot.models import DEFAULT_JSON_PATH, DEFAULT_DB_PATH

if __name__ == "__main__":
    build_index(DEFAULT_JSON_PATH, DEFAULT_DB_PATH)
```

- [ ] **Step 3: Run index build**

Run: `python build_index.py`
Expected output:
```
Loading model intfloat/multilingual-e5-large...
Encoding ~5000 records...
[progress bar]
Writing to index.db...
Index built: ~5000 records in index.db
```
Expected: `index.db` file created, ~50-200MB depending on embeddings

- [ ] **Step 4: Verify database contents**

Run: `python -c "import sqlite3; db=sqlite3.connect('index.db'); print('faqs:', db.execute('SELECT COUNT(*) FROM faqs').fetchone()[0]); print('embeddings:', db.execute('SELECT COUNT(*) FROM faq_embeddings').fetchone()[0])"`
Expected: `faqs: ~5000`, `embeddings: ~5000` (same number)

- [ ] **Step 5: Commit**

```bash
git add qa_bot/indexer.py build_index.py index.db
git commit -m "feat: indexer with SQLite + embedding storage"
```

Note: Add `index.db` to `.gitignore` in a real project. For MVP, include it so the bot works out of the box.

---

### Task 3: Retriever

**Files:**
- Create: `qa_bot/retriever.py`

- [ ] **Step 1: Write retriever module**

Create `qa_bot/retriever.py`:

```python
from __future__ import annotations

import sqlite3

import numpy as np
from sentence_transformers import SentenceTransformer, util

from qa_bot.models import FAQEntry, SearchResult, MODEL_NAME, DEFAULT_DB_PATH


class Retriever:
    """Semantic search over FAQ embeddings."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH, model_name: str = MODEL_NAME):
        self.db_path = db_path
        self.model = SentenceTransformer(model_name)
        self._load_embeddings()

    def _load_embeddings(self) -> None:
        """Load all FAQ embeddings from SQLite into memory."""
        db = sqlite3.connect(self.db_path)
        cur = db.cursor()

        cur.execute("SELECT id, hauptthema, subthema, frage, kanal, antwort FROM faqs")
        rows = cur.fetchall()

        cur.execute("SELECT faq_id, embedding FROM faq_embeddings")
        emb_rows = {row[0]: np.frombuffer(row[1], dtype=np.float32) for row in cur.fetchall()}

        db.close()

        self.entries: list[FAQEntry] = []
        embeddings = []

        for row in rows:
            faq_id, hauptthema, subthema, frage, kanal, antwort = row
            self.entries.append(FAQEntry(
                id=faq_id,
                hauptthema=hauptthema,
                subthema=subthema,
                frage=frage,
                kanal=kanal,
                antwort=antwort,
            ))
            embeddings.append(emb_rows[faq_id])

        self.embedding_matrix: np.ndarray = np.stack(embeddings)

    def search(
        self,
        query: str,
        top_k: int = 5,
        channel: str | None = None,
    ) -> list[SearchResult]:
        """Search for FAQs matching the query.

        Args:
            query: User's question
            top_k: Number of results to return
            channel: Optional channel filter (e.g. "telefonisch")

        Returns:
            List of SearchResult sorted by similarity score
        """
        query_emb = self.model.encode(query, convert_to_numpy=True)

        if channel:
            # Filter entries by channel
            mask = np.array([e.kanal == channel for e in self.entries])
            filtered_embeddings = self.embedding_matrix[mask]
            filtered_entries = [e for e, m in zip(self.entries, mask) if m]
        else:
            filtered_embeddings = self.embedding_matrix
            filtered_entries = self.entries

        scores = util.cos_sim(query_emb, filtered_embeddings)[0].cpu().numpy()
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] < 0:  # Skip negative similarities
                break
            results.append(SearchResult(
                entry=filtered_entries[int(idx)],
                score=float(scores[idx]),
            ))

        return results
```

- [ ] **Step 2: Test retriever interactively**

Run: `python -c "
from qa_bot.retriever import Retriever
r = Retriever()
results = r.search('Ich bin schwanger, wann bekomme ich Mutterschaftsgeld?')
for res in results:
    print(f'{res.score:.3f} [{res.entry.kanal}] {res.entry.frage}')
"`
Expected: Top results related to Mutterschaftsgeld/Schwangerschaft with scores > 0.3

- [ ] **Step 3: Test retriever with channel filter**

Run: `python -c "
from qa_bot.retriever import Retriever
r = Retriever()
results = r.search('Ich bin schwanger', channel='telefonisch')
for res in results:
    print(f'{res.score:.3f} [{res.entry.kanal}] {res.entry.frage}')
print(f'Total results: {len(results)}')
"`
Expected: Only results with kanal="telefonisch"

- [ ] **Step 4: Commit**

```bash
git add qa_bot/retriever.py
git commit -m "feat: retriever with semantic search and channel filter"
```

---

### Task 4: CLI Interface

**Files:**
- Create: `cli.py`

- [ ] **Step 1: Create CLI**

Create `cli.py`:

```python
#!/usr/bin/env python3
"""QA Bot CLI. Usage: python cli.py "Your question?" [--top-k 5] [--channel telefonisch]"""

import argparse
import sys

from qa_bot.retriever import Retriever
from qa_bot.models import DEFAULT_TOP_K


def main():
    parser = argparse.ArgumentParser(description="AOK Wissensportal QA-Bot")
    parser.add_argument("query", nargs="?", help="Your question")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K, help="Number of results")
    parser.add_argument("--channel", type=str, default=None, help="Filter by channel")
    args = parser.parse_args()

    if not args.query:
        print("Usage: python cli.py \"Your question?\" [--top-k 5] [--channel telefonisch]")
        sys.exit(1)

    retriever = Retriever()
    results = retriever.search(args.query, top_k=args.top_k, channel=args.channel)

    if not results:
        print("Keine Treffer gefunden.")
        return

    print(f"Top-{len(results)} Treffer für: {args.query!r}\n")
    for i, res in enumerate(results, 1):
        print(f"{i}. [Score: {res.score:.3f}] {res.entry.frage}")
        print(f"   Thema: {res.entry.hauptthema} / {res.entry.subthema}")
        print(f"   Kanal: {res.entry.kanal}")
        print(f"   Antwort: {res.entry.antwort[:200]}...")
        print()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test CLI with various queries**

Run: `python cli.py "Ich bin schwanger, wann bekomme ich Mutterschaftsgeld?"`
Expected: Shows top-5 results related to Mutterschaftsgeld

Run: `python cli.py "Geld wenn Baby kommt" --top-k 3`
Expected: Should still find Mutterschaftsgeld/Schwangerschaft results (semantic match)

Run: `python cli.py "Krankengeld beantragen" --channel telefonisch`
Expected: Only results with kanal="telefonisch"

Run: `python cli.py`
Expected: Usage message and exit code 1

- [ ] **Step 3: Commit**

```bash
git add cli.py
git commit -m "feat: CLI interface for FAQ queries"
```

---

### Task 5: FastAPI Server

**Files:**
- Create: `server.py`

- [ ] **Step 1: Create FastAPI server**

Create `server.py`:

```python
#!/usr/bin/env python3
"""FastAPI server for the AOK Wissensportal QA-Bot."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Body
from pydantic import BaseModel

from qa_bot.retriever import Retriever
from qa_bot.models import DEFAULT_TOP_K


class QueryRequest(BaseModel):
    question: str
    channel: str | None = None
    top_k: int = DEFAULT_TOP_K


retriever: Retriever | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global retriever
    retriever = Retriever()
    yield


app = FastAPI(title="AOK Wissensportal QA-Bot", lifespan=lifespan)


def _format_results(results):
    return {
        "query": results[0],
        "results": [
            {
                "score": r.score,
                "frage": r.entry.frage,
                "antwort": r.entry.antwort,
                "kanal": r.entry.kanal,
                "hauptthema": r.entry.hauptthema,
                "subthema": r.entry.subthema,
            }
            for r in results[1]
        ],
    } if results else {"query": "", "results": []}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/query")
def query(
    q: str = Query(..., min_length=1, description="User's question"),
    channel: str | None = Query(None, description="Filter by channel"),
    top_k: int = Query(DEFAULT_TOP_K, ge=1, le=20, description="Number of results"),
):
    global retriever
    results = retriever.search(q, top_k=top_k, channel=channel)
    return {
        "query": q,
        "results": [
            {
                "score": r.score,
                "frage": r.entry.frage,
                "antwort": r.entry.antwort,
                "kanal": r.entry.kanal,
                "hauptthema": r.entry.hauptthema,
                "subthema": r.entry.subthema,
            }
            for r in results
        ],
    }


@app.post("/query")
def query_post(request: QueryRequest):
    global retriever
    results = retriever.search(request.question, top_k=request.top_k, channel=request.channel)
    return {
        "query": request.question,
        "results": [
            {
                "score": r.score,
                "frage": r.entry.frage,
                "antwort": r.entry.antwort,
                "kanal": r.entry.kanal,
                "hauptthema": r.entry.hauptthema,
                "subthema": r.entry.subthema,
            }
            for r in results
        ],
    }
```

- [ ] **Step 2: Start server and test**

Run: `uvicorn server:app --reload --port 8000`
Expected: Server starts on http://localhost:8000

Run: `curl "http://localhost:8000/health"`
Expected: `{"status":"ok"}`

Run: `curl "http://localhost:8000/query?q=Ich+bin+schwanger&top_k=3"`
Expected: JSON with query results

Run: `curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"question":"Krankengeld beantragen","top_k":3}'`
Expected: JSON with query results (same format as GET)

Open: http://localhost:8000/docs
Expected: Swagger UI with interactive API docs

- [ ] **Step 3: Commit**

```bash
git add server.py
git commit -m "feat: FastAPI server with /query endpoint"
```

---

### Task 6: .gitignore and final cleanup

**Files:**
- Create: `.gitignore`

- [ ] **Step 1: Create .gitignore**

```gitignore
__pycache__/
*.pyc
.env
index.db
.venv/
```

- [ ] **Step 2: Final verification**

Run: `python cli.py "Wie viel Krankengeld bekomme ich?"`
Run: `python cli.py "Fitnessstudio Zuschuss" --top-k 3`
Run: `python cli.py "Brille zahlt die Kasse"`

All should return relevant results with scores > 0.2.

- [ ] **Step 3: Final commit**

```bash
git add .gitignore
git commit -m "chore: add gitignore and finalize MVP"
```
