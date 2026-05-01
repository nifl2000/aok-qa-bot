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

    print(f"Top-{len(results)} Treffer fur: {args.query!r}\n")
    for i, res in enumerate(results, 1):
        print(f"{i}. [Score: {res.score:.3f}] {res.entry.frage}")
        print(f"   Thema: {res.entry.hauptthema} / {res.entry.subthema}")
        print(f"   Kanal: {res.entry.kanal}")
        print(f"   Antwort: {res.entry.antwort[:200]}...")
        print()


if __name__ == "__main__":
    main()
