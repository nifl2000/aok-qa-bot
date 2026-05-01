# AOK Wissensportal QA-Bot

Lokaler FAQ-Bot mit Embedding-Suche und LLM-Reranking.

## Starten

```bash
python ask.py
```

## Voraussetzungen

```bash
pip install sentence-transformers httpx numpy
```

## Konfiguration

API-Key in `.env` oder als Environment-Variable:

```
LLM_API_KEY=sk-...
```

## Architektur

- **Embedding-Modell:** `intfloat/multilingual-e5-large`
- **LLM-Reranking:** `kimi-k2.5` via Alibaba Coding Plan API
- **Index:** SQLite mit FTS5 + Embedding-Speicher (~1400 deduplizierte Einträge)

## Index neu bauen

```bash
python -c "from qa_bot.indexer import build_index; build_index('input/Wissensportal_Hierarchisch_KOMPLETT_bereinigt.json', 'index.db')"
```
