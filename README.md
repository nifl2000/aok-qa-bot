# AOK Wissensportal QA-Bot

Lokaler FAQ-Bot mit Embedding-Suche und LLM-Reranking für die AOK Sachsen-Anhalt.

## Features

- **Context-Aware Embeddings:** Suche über 1.400 deduplizierte FAQ-Einträge im Format `{Kategorie}: {Frage}` für maximale semantische Präzision.
- **Default LLM-Reranking:** Automatisches Reranking der Top-20 Kandidaten via `kimi-k2.5` für präziseste Ergebnisse.
- **Antwort-Vorschau:** Bereinigte Formatierung und intelligente Kürzung der FAQ-Antworten.
- **Einfache Konfiguration:** Unterstützung für `.env`-Dateien.
- **Automatischer Index-Build:** Datenbank wird beim ersten Start automatisch aus den Quelldaten erzeugt.

## Schnellstart

1. Repositorium klonen:
   ```bash
   git clone https://github.com/nifl2000/aok-qa-bot.git
   cd aok-qa-bot
   ```

2. Umgebung einrichten und Abhängigkeiten installieren:
   ```bash
   # Empfohlen: uv oder venv nutzen
   pip install -r requirements.txt
   ```

3. Konfiguration:
   Kopiere die `.env.example` nach `.env` und trage deinen API-Key ein:
   ```bash
   cp .env.example .env
   # LLM_API_KEY=sk-sp-...
   ```

4. Bot starten:
   ```bash
   python ask.py
   ```

## Erster Start

Beim ersten Start passieren drei Dinge automatisch:
1. **Modell-Download** (~2.2 GB, einmalig) — `intfloat/multilingual-e5-large` wird lokal gespeichert.
2. **Index-Build** (~20 Sekunden) — Erstellt die SQLite-Datenbank `index.db` mit Kategorie-basierten Embeddings.
3. **Suche bereit** — Die interaktive CLI startet sofort.

## Konfiguration

Die Konfiguration erfolgt primär über die `.env`-Datei:

| Variable | Beschreibung | Standard |
|---|---|---|
| `LLM_API_KEY` | API-Key für LLM-Reranking (erforderlich) | - |
| `MODEL_NAME` | Embedding-Modell von Hugging Face | `intfloat/multilingual-e5-large` |
| `DEFAULT_DB_PATH` | Pfad zur SQLite-Datenbank | `index.db` |

## Architektur

Das System nutzt eine zweistufige Suche für optimale Performance und Qualität:

```
Frage → Embedding-Suche (Top-20) → LLM-Reranking (Kimi-k2.5) → Top-3 Ergebnisse
```

- **Embedding:** `intfloat/multilingual-e5-large` (Vektoren basieren auf `Kategorie: Frage`).
- **LLM-Reranking:** `kimi-k2.5` (Standardmäßig aktiv).
- **Datenbank:** SQLite mit FTS5-Erweiterung.

## Web-Anwendung

Das Projekt enthält nun eine vollständige Web-Anwendung.

### Architektur
- **Backend:** FastAPI (Python) auf Port 8000.
- **Frontend:** React (TypeScript) + Vite auf Port 5173.

### Start der Web-App

1. **Backend starten:**
   ```bash
   cd aok-qa-bot
   # LLM_API_KEY muss in .env stehen
   python backend/main.py
   ```

2. **Frontend starten:**
   ```bash
   cd aok-qa-bot/frontend
   npm install
   npm run dev
   ```

3. Öffne [http://localhost:5173](http://localhost:5173) in deinem Browser.

## Projektstruktur

```
ask.py                          ← Hauptprogramm (interaktive CLI)
build_index.py                  ← Script zum manuellen Neuaufbau des Index
evaluate.py                     ← Quantitative Evaluation (Recall/MRR Messung)
eval_set.py                     ← Test-Daten-Set (50 Query Golden Set)
.env.example                    ← Vorlage für Umgebungsvariablen
qa_bot/
  config.py                     ← Zentrale Konfiguration & .env Loader
  indexer.py                    ← Datenverarbeitung & Embedding-Generierung
  models.py                     ← Pydantic-Modelle & Datenstrukturen
  retriever.py                  ← Such-Logik (Hybrid & LLM-Rerank)
  text_utils.py                 ← Text-Bereinigung & Formatierung
  topic_filter.py               ← Automatische Themen-Erkennung
input/
  Wissensportal_Hierarchisch_...json  ← Quelldaten der AOK
tests/                          ← Umfassende Unit- & Integrationstests
```

## Qualität & Evaluation

Die Qualität wird mit `evaluate.py` gegen das Golden Set gemessen:

| Methode | Recall@1 | Recall@3 | MRR |
|---|---|---|---|
| Embedding (nur Frage) | 46% | 62% | 0.54 |
| **Embedding (Thema: Frage)** | **68%** | **88%** | **0.78** |
| **+ LLM Reranking** | **91%** | **97%** | **0.94** |

## Tests

```bash
pip install pytest
pytest tests/ -v
```
