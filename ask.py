#!/usr/bin/env python3
"""Interactive CLI for the AOK Wissensportal QA-Bot.

Usage: python ask.py
Then type questions at the prompt. Press Enter on empty line to quit.
"""

import os
import sys
import logging
import warnings

# Suppress all HF Hub warnings and progress bars
os.environ["HF_HUB_VERBOSITY"] = "critical"
os.environ["TQDM_DISABLE"] = "1"
logging.getLogger("huggingface_hub").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore")

from qa_bot.config import llm_api_key, DEFAULT_DB_PATH
from qa_bot.indexer import ensure_index
from qa_bot.retriever import Retriever
from qa_bot.text_utils import clean_answer, format_score, truncate_at_word


def _validate_startup() -> None:
    """Check prerequisites and exit with clear messages."""
    if not llm_api_key():
        print("Fehler: LLM_API_KEY nicht gesetzt.")
        print("Bitte als Umgebungsvariable definieren: export LLM_API_KEY=sk-...")
        sys.exit(1)

    ensure_index()
    if not os.path.exists(DEFAULT_DB_PATH):
        print(f"Fehler: Index-Datei '{DEFAULT_DB_PATH}' nicht gefunden.")
        print("Baue den Index mit: python build_index.py")
        sys.exit(1)


def main() -> None:
    _validate_startup()

    print("AOK Wissensportal QA-Bot")
    print("Lade Modell...", end=" ", flush=True)

    retriever = Retriever()

    print("\r" + " " * 60 + "\r", end="")
    print("AOK Wissensportal QA-Bot (kimi-k2.5 Reranking)")
    print("Tippe eine Frage ein. Leere Zeile beendet.\n")

    while True:
        try:
            query = input("Frage> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nTschau!")
            break

        if not query:
            print("Tschau!")
            break

        try:
            results = retriever.search(
                query, top_k=3, llm_rerank=True, llm_rerank_top_k=20
            )
        except Exception as e:
            print(f"Fehler: {e}\n")
            continue

        if not results:
            print("Keine Treffer gefunden.\n")
            continue

        for i, res in enumerate(results, 1):
            answer = res.entry.answers[0].antwort if res.entry.answers else ""
            answer = clean_answer(answer)
            preview = truncate_at_word(answer, 200)

            print(f"\n{'─' * 60}")
            print(f"  {i}. Treffer  |  Relevanz: {format_score(res.score)}")
            print(f"  Thema: {res.entry.hauptthema}")
            print(f"  {res.entry.frage}")
            print(f"\n  {preview}")

        print(f"\n{'─' * 60}\n")


if __name__ == "__main__":
    main()
