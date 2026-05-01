# AOK Wissensportal QA-Bot

Lokaler FAQ-Bot mit Embedding-Suche und LLM-Reranking für die AOK Sachsen-Anhalt.

## Features

- **Embedding-Suche** über 1.400 deduplizierte FAQ-Einträge (multilingual-e5-large)
- **LLM-Reranking** der Top-20 Kandidaten (kimi-k2.5) → 92% Recall@1
- **Antwort-Vorschau** mit bereinigter Formatierung (200 Zeichen)
- **Automatischer Index-Build** beim ersten Start

## Schnellstart

```bash
git clone https://github.com/nifl2000/aok-qa-bot.git
cd aok-qa-bot
pip install -r requirements.txt
export LLM_API_KEY=sk-...
python ask.py
```

## Erster Start

Beim ersten Start passieren drei Dinge automatisch:

1. **Modell-Download** (~2.2 GB, einmalig) — `intfloat/multilingual-e5-large` wird von Hugging Face in den lokalen Cache geladen
2. **Index-Build** (~20 Sekunden) — Aus den Quelldaten in `input/` wird die SQLite-Datenbank `index.db` gebaut
3. **Suche bereit** — Ab jetzt startet die App sofort

## Konfiguration

| Umgebungsvariable | Beschreibung | Beispiel |
|---|---|---|
| `LLM_API_KEY` | API-Key für LLM-Reranking (erforderlich) | `sk-sp-abc123...` |

## Architektur

```
Frage → Embedding-Suche (Top-20) → LLM-Reranking → Top-3 Ergebnisse
```

| Komponente | Modell / Technologie |
|---|---|
| Embedding | `intfloat/multilingual-e5-large` |
| LLM-Reranking | `kimi-k2.5` via Alibaba Coding Plan API |
| Index | SQLite mit FTS5 + Embedding-Speicher |
| Antwort-Bereinigung | `qa_bot/text_utils.py` |

## Projektstruktur

```
ask.py                          ← Startpunkt (CLI)
build_index.py                  ← Index manuell neu bauen
eval_set.py                     ← 50-Query Golden Set (Evaluation)
qa_bot/
  config.py                     ← Zentrale Konfiguration + Env-Variablen
  indexer.py                    ← Index-Erzeugung (Deduplizierung + Embeddings)
  models.py                     ← Datenmodelle (FAQEntry, SearchResult)
  retriever.py                  ← Suche (Embedding, BM25, Hybrid, LLM-Rerank)
  text_utils.py                 ← Text-Bereinigung und Formatierung
  topic_filter.py               ← Automatische Topic-Erkennung
input/
  Wissensportal_Hierarchisch_...json  ← Quelldaten (FAQ-Hierarchie)
tests/                          ← Unit-Tests (40 Tests)
requirements.txt                ← Python-Abhängigkeiten
```

## Index neu bauen

```bash
python build_index.py
```

Oder direkt in Python:

```python
from qa_bot.indexer import build_index
build_index("input/Wissensportal_Hierarchisch_KOMPLETT_bereinigt.json", "index.db")
```

## Tests

```bash
pip install pytest
pytest tests/ -v
```

## Qualitätsmetriken

| Methode | Recall@1 | Recall@3 | MRR |
|---|---|---|---|
| Embedding-only | 70% | 80% | 0.75 |
| + LLM Reranking (kimi-k2.5) | **92%** | **98%** | **0.93** |
