#!/usr/bin/env python3
"""QA Bot CLI. Usage: python cli.py "Your question?" [--top-k 5] [--channel telefonisch] [--topic Mutterschaftsgeld]"""

import argparse
import sys

from qa_bot.retriever import Retriever
from qa_bot.models import DEFAULT_TOP_K


def main() -> None:
    parser = argparse.ArgumentParser(description="AOK Wissensportal QA-Bot")
    parser.add_argument("query", nargs="?", help="Your question")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K, help="Number of results")
    parser.add_argument("--channel", type=str, default=None, help="Filter by channel")
    parser.add_argument("--topic", type=str, default=None, help="Filter by topic (hauptthema)")
    parser.add_argument("--rerank", action="store_true", help="Use cross-encoder reranking")
    args = parser.parse_args()

    if not args.query:
        print("Usage: python cli.py \"Your question?\" [--top-k 5] [--channel telefonisch] [--topic Thema]")
        sys.exit(1)

    retriever = Retriever()
    try:
        results = retriever.search(
            args.query, top_k=args.top_k, channel=args.channel, topic=args.topic,
            rerank=args.rerank,
        )
    except Exception as e:
        print(f"Fehler bei der Suche: {e}")
        sys.exit(1)

    if not results:
        print("Keine Treffer gefunden.")
        return

    print(f"Top-{len(results)} Treffer fuer: {args.query!r}\n")
    for i, res in enumerate(results, 1):
        scores = []
        if res.rerank_score > 0:
            scores.append(f"rerank={res.rerank_score:.2f}")
        if res.bm25_score > 0:
            scores.append(f"bm25={res.bm25_score:.1f}")
        if res.embed_score > 0:
            scores.append(f"embed={res.embed_score:.4f}")
        scores_str = f" ({', '.join(scores)})" if scores else ""
        print(f"{i}. [rrf={res.score:.3f}{scores_str}] {res.entry.frage}")
        print(f"   Thema: {res.entry.hauptthema} / {res.entry.subthema}")
        for answer in res.entry.answers:
            print(f"   [{answer.kanal}] {answer.antwort[:200]}...")
        print()


if __name__ == "__main__":
    main()
