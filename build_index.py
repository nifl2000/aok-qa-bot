#!/usr/bin/env python3
"""Build the FAQ embedding index. Usage: python build_index.py"""

from qa_bot.indexer import build_index
from qa_bot.models import DEFAULT_JSON_PATH, DEFAULT_DB_PATH

if __name__ == "__main__":
    build_index(DEFAULT_JSON_PATH, DEFAULT_DB_PATH)
