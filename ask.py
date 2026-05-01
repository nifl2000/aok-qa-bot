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

from qa_bot.retriever import Retriever


import re


def _clean_answer(text: str) -> str:
    """Clean up scraped answer text: fix hard line breaks and missing spaces."""
    # Replace hard line breaks with spaces
    text = text.replace("\n", " ")
    # Collapse multiple spaces
    text = re.sub(r"  +", " ", text)
    # Fix missing space after sentence-ending punctuation before uppercase
    # e.g. "Kalenderjahr.Hinweis:Der" → "Kalenderjahr. Hinweis: Der"
    text = re.sub(r"([.!?])([A-ZÄÖÜ])", r"\1 \2", text)
    text = re.sub(r":([A-ZÄÖÜ])", r": \1", text)
    return text.strip()


def _truncate_at_word(text: str, max_len: int) -> str:
    """Truncate text at max_len, breaking at a word boundary."""
    if len(text) <= max_len:
        return text
    truncated = text[:max_len].rstrip()
    # Cut back to last word boundary
    last_space = truncated.rfind(" ")
    if last_space > max_len * 0.6:  # only if we don't lose too much
        truncated = truncated[:last_space]
    return truncated + " ..."


def _format_score(score: float) -> str:
    """Format LLM score (0-10) with a short relevance label."""
    if score >= 8:
        label = "sehr relevant"
    elif score >= 5:
        label = "relevant"
    elif score >= 3:
        label = "teilweise relevant"
    else:
        label = "wenig relevant"
    return f"{score:.0f}/10 — {label}"


def main() -> None:
    print("AOK Wissensportal QA-Bot")
    print("Lade Modell...", end=" ", flush=True)

    retriever = Retriever(
        llm_api_key=os.environ.get("LLM_API_KEY"),
    )

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
            answer = _clean_answer(answer)
            preview = _truncate_at_word(answer, 200)

            print(f"\n{'─' * 60}")
            print(f"  {i}. Treffer  |  Relevanz: {_format_score(res.score)}")
            print(f"  Thema: {res.entry.hauptthema}")
            print(f"  {res.entry.frage}")
            print(f"\n  {preview}")

        print(f"\n{'─' * 60}\n")


if __name__ == "__main__":
    main()
