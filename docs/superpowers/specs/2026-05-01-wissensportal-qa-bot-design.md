# MVP Design: AOK Wissensportal QA-Bot

## Purpose
Lokaler QA-Bot der AOK-Wissensportal-Daten (1400 FAQs, 4992 kanalisierte Antworten) für schnelle semantische Suche durch Mitarbeiter.

## Core Decision
- **Embedding-only auf Fragetiteln**, nicht auf Antworttexten (Antworten sind Link-Listen ohne semantische Struktur)
- **Kein LLM/RAG** — nur Retrieval, deterministisch, keine Halluzinationen
- **Hybrid-Ansatz:** Embedding-Suche + optionaler Kanal-Filter (Keyword-Match)

## Architecture

```
input/                              JSON-Daten (bereits vorhanden)
├── index.db                        SQLite-Datenbank mit Embeddings (generiert)
├── qa_bot/
│   ├── __init__.py
│   ├── indexer.py                  JSON → Embeddings → SQLite
│   └── retriever.py                Query → Embedding → Top-K Suche
├── build_index.py                  Einmal-Skript: python build_index.py
├── cli.py                          Terminal-Interface
├── server.py                       FastAPI Server mit /query Endpoint
└── requirements.txt
```

## Components

### 1. Indexer (`qa_bot/indexer.py`)
- Lädt JSON, extrahiert alle (frage, hauptthema, subthema, kanal, antwort)-Tupel
- Verwendet `intfloat/multilingual-e5-large` für Embeddings
- Speichert in SQLite:
  - `faqs`: id, hauptthema, subthema, frage, kanal, antwort
  - `faq_embeddings`: faq_id, embedding (BLOB, numpy array)
- Einmalige Build-Zeit: ~30-60s

### 2. Retriever (`qa_bot/retriever.py`)
- Embeddet User-Frage mit demselben Modell
- Berechnet Cosine Similarity gegen alle gespeicherten Embeddings
- Gibt Top-K Ergebnisse zurück mit Score, Frage, Antwort, Kanal, Thema
- Optionaler Kanal-Filter: schränkt Suche auf bestimmten Kanal ein
- Latenz: ~10-15ms pro Query

### 3. CLI (`cli.py`)
- `python cli.py "Frage?"` → zeigt Top-5 Treffer mit Score und Antwort
- Optional: `--channel telefonisch`, `--top-k 10`

### 4. FastAPI Server (`server.py`)
- `GET /query?q=Frage&channel=telefonisch&top_k=5`
- `POST /query` mit JSON-Body
- Uvicorn: `uvicorn server:app --reload`

## Embedding Model
- **`intfloat/multilingual-e5-large`** — stärkstes multilinguales Modell für Deutsch
- 1024 Dimensionen, ~550MB Modellgröße
- ~15ms Inference auf CPU
- Gut bei Fachbegriffen (AAG, U2, KVdR) und langen Fragen (80-150 Zeichen)

## Dependencies
- `sentence-transformers` (lädt Modell automatisch)
- `fastapi[standard]` (nur server.py)
- `numpy` (Cosine Similarity)
- `sqlite3` (built-in)

## Deployment Path
- Lokal: `python cli.py` oder `uvicorn server:app`
- Cloudflare Workers: Retrieval-Modul bleibt, Serving-Layer wird zu Hono/Workers
- Eigener Server: Docker-Container mit uvicorn
