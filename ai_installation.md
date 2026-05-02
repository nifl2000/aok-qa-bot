# AI Install Guide — AOK QA-Bot

Dieses Dokument ist für AI-Assistenten (Gemini CLI, Claude Code, Open Source Agents) gedacht,
um das Projekt auf einem frischen System zu installieren und lauffähig zu machen.

## Systemvoraussetzungen

| Komponente | Mindestversion |
|---|---|
| Python | >= 3.11 |
| Node.js | >= 20 |
| npm | >= 10 |
| Git | >= 2.40 |
| RAM | 8 GB (16 GB empfohlen) |
| Festplatte | ~3 GB frei (Modell ~2.2 GB + Dependencies) |

## Installation

### Schritt 1: Repository klonen

```bash
git clone https://github.com/nifl2000/aok-qa-bot.git
cd aok-qa-bot
```

### Schritt 2: Python-Abhängigkeiten installieren

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest
```

### Schritt 3: Frontend-Abhängigkeiten installieren

```bash
cd frontend
npm install
cd ..
```

### Schritt 4: Konfiguration

```bash
cp .env.example .env
# In .env eintragen: LLM_API_KEY=sk-sp-...
```

### Schritt 5: Tests ausführen

```bash
pytest tests/ -v
cd frontend && npm test && cd ..
```

### Schritt 6: Backend starten

```bash
python backend/main.py
```

Das Backend lädt beim ersten Start automatisch:
- Embedding-Modell (~2.2 GB) von HuggingFace
- Erstellt `index.db` aus den Quelldaten (`input/`)

Warten bis `Backend ready.` erscheint.

### Schritt 7: Frontend starten

```bash
cd frontend
npm run dev
```

Öffne http://localhost:5173 im Browser.

## Docker

```bash
docker build -t aok-qa-bot .
docker run -p 8000:8000 --env-file .env aok-qa-bot
```

## Struktur

```
.
├── backend/main.py          ← FastAPI Backend
├── frontend/                ← React + Vite Frontend
│   ├── src/App.tsx          ← Hauptkomponente
│   └── src/App.test.tsx     ← Tests
├── qa_bot/                  ← Core-Paket
│   ├── config.py            ← Konfiguration
│   ├── indexer.py           ← Index-Build
│   ├── retriever.py         ← Such-Logik
│   ├── text_utils.py        ← Text-Bereinigung
│   └── topic_filter.py      ← Themen-Erkennung
├── input/                   ← Quelldaten (JSON)
├── tests/                   ← Python Tests
├── Dockerfile               ← Container
├── requirements.txt         ← Python Dependencies
├── pyproject.toml           ← Projekt-Metadaten
├── .env.example             ← Konfigurations-Vorlage
└── ai_installation.md       ← Dieses Dokument
```

## API

| Endpoint | Methode | Auth | Beschreibung |
|---|---|---|---|
| `/api/health` | GET | Nein | Backend-Status |
| `/api/ready` | GET | Nein | Readiness-Prüfung |
| `/api/v1/search` | POST | `X-Password` Header | FAQ-Suche |

### Beispiel: Search Request

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -H "X-Password: aok2026" \
  -d '{"query": "Was ist Mutterschaftsgeld?", "top_k": 3}'
```

## Umgebungsvariablen

| Variable | Beschreibung | Standard |
|---|---|---|
| `LLM_API_KEY` | API-Key für LLM-Reranking | - |
| `AOK_BOT_PASSWORD` | Passwort für API-Zugriff | `aok2026` |
| `ALLOWED_ORIGINS` | CORS erlaubte Origins | `http://localhost:5173` |
| `VITE_API_URL` | Frontend API URL | `http://localhost:8000` |
| `VITE_API_PASSWORD` | Frontend API Passwort | `aok2026` |

## Troubleshooting

| Problem | Lösung |
|---|---|
| `ModuleNotFoundError: No module named 'qa_bot'` | Von Repo-Root ausführen, nicht aus `backend/` |
| `Port 8000 already in use` | `lsof -i :8000` und Prozess killen |
| Frontend findet API nicht | `VITE_API_URL` in `.env` setzen |
| Modell lädt nicht | Internetverbindung prüfen, HF_TOKEN setzen |
| LLM-Reranking crasht | `LLM_API_KEY` in `.env` prüfen |
