from __future__ import annotations

import re


def clean_answer(text: str) -> str:
    """Clean up FAQ answers into a single continuous flow of text."""
    if not text:
        return ""

    # 1. Fix concatenated words like "smartAZuB" or "AuszahlungFremdkunde"
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    text = text.replace("AZu B", "AZuB")

    # 2. Replace all newlines and tabs with spaces
    text = text.replace("\n", " ").replace("\t", " ")
    
    # 3. Fix missing spaces after punctuation
    text = re.sub(r"([.!?])([A-ZÄÖÜ])", r"\1 \2", text)
    text = re.sub(r":([A-ZÄÖÜ])", r": \1", text)
    text = re.sub(r"(\d)\.([A-ZÄÖÜ])", r"\1. \2", text)

    # 4. Collapse multiple spaces
    text = re.sub(r"  +", " ", text)

    return text.strip()


def truncate_at_word(text: str, max_len: int) -> str:
    """Truncate text at max_len, breaking at a word boundary."""
    if len(text) <= max_len:
        return text
    truncated = text[:max_len].rstrip()
    last_space = truncated.rfind(" ")
    if last_space > max_len * 0.6:
        truncated = truncated[:last_space]
    return truncated + " ..."


def format_score(score: float) -> str:
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
