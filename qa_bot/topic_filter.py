from __future__ import annotations

import re
import sqlite3
from collections import Counter

from qa_bot.models import DEFAULT_DB_PATH

_STOP_WORDS = frozenset({
    "ich", "die", "der", "und", "ein", "eine", "einen", "einem", "einer",
    "ist", "wie", "was", "kann", "muss", "wird", "bin", "bei", "für",
    "den", "das", "dem", "des", "von", "mit", "nicht", "auch", "wenn",
    "werden", "mein", "meine", "meinen", "meiner", "mir",
    "sich", "nach", "noch", "nur", "oder", "aber", "als",
    "da", "dann", "doch", "hier", "man", "sehr", "so", "um", "uns",
    "viel", "wann", "wer", "wo", "zu", "zum", "zur", "über",
    "aok", "san", "sachsen", "anhalt",
    "bekomme", "brauche", "kriege", "will", "machen", "geht", "stellen",
    "wissen", "bedeutet", "bedeutung", "eigentlich", "genau", "frage",
    "fragen", "leisten", "leistung", "kosten", "beitrag", "beitrage",
})


def _extract_words(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-zA-ZäöüÄÖÜß]{3,}", text.lower()) if w not in _STOP_WORDS]


class TopicFilter:
    """Detect topic from a query using FTS5-based matching.

    Uses the FTS5 index to find matching FAQs, then infers the dominant
    topic among the top matches. More robust than TF-IDF because it uses
    the actual indexed FAQ data rather than abstract topic-word scores.
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self._db_path = db_path

    def detect(self, query: str, top_n: int = 20) -> str | None:
        """Detect topic for a query. Returns topic name or None if ambiguous.

        Strategy: Run FTS5 search, look at the dominant topic among top_n results.
        If >= 60% of top results share the same topic, return it.
        """
        words = _extract_words(query)
        if not words:
            return None

        with sqlite3.connect(self._db_path) as db:
            cur = db.cursor()
            # Build FTS5 query with OR semantics for all words
            fts_query = " OR ".join(words)
            cur.execute(
                "SELECT rowid, frage, hauptthema, rank "
                "FROM faqs_fts WHERE faqs_fts MATCH ? "
                "ORDER BY rank LIMIT ?",
                (fts_query, top_n),
            )
            rows = cur.fetchall()

        if len(rows) < 3:
            # Too few matches to be meaningful
            return None

        # Count topics among top results
        topic_counts = Counter(row[2] for row in rows)
        total = len(rows)

        # Check if any topic dominates
        most_common_topic, most_common_count = topic_counts.most_common(1)[0]
        dominance = most_common_count / total

        # Require at least 50% agreement among top results for auto-detection
        if dominance >= 0.5:
            return most_common_topic

        return None

    @staticmethod
    def normalize_topic(topic: str) -> str:
        """Normalize a topic name for comparison.

        Handles umlaut replacements (ä→ae, ö→oe, ü→ue, ß→ss)
        to match the eval_set convention.
        """
        mapping = {"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue", "ß": "ss"}
        for k, v in mapping.items():
            topic = topic.replace(k, v)
        return topic
