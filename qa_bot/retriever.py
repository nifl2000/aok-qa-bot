from __future__ import annotations

import sqlite3

import numpy as np
from sentence_transformers import SentenceTransformer, util

from qa_bot.models import FAQEntry, SearchResult, MODEL_NAME, DEFAULT_DB_PATH


class Retriever:
    """Semantic search over FAQ embeddings."""

    entries: list[FAQEntry]
    embedding_matrix: np.ndarray

    def __init__(self, db_path: str = DEFAULT_DB_PATH, model_name: str = MODEL_NAME):
        self.db_path = db_path
        self.model = SentenceTransformer(model_name)
        self._load_embeddings()

    def _load_embeddings(self) -> None:
        """Load all FAQ embeddings from SQLite into memory."""
        with sqlite3.connect(self.db_path) as db:
            cur = db.cursor()

            cur.execute("SELECT id, hauptthema, subthema, frage, kanal, antwort FROM faqs")
            rows = cur.fetchall()

            cur.execute("SELECT faq_id, embedding FROM faq_embeddings")
            emb_rows = {row[0]: np.frombuffer(row[1], dtype=np.float32) for row in cur.fetchall()}

        self.entries = []
        embeddings = []

        for row in rows:
            faq_id, hauptthema, subthema, frage, kanal, antwort = row
            if faq_id not in emb_rows:
                continue
            self.entries.append(FAQEntry(
                id=faq_id,
                hauptthema=hauptthema,
                subthema=subthema,
                frage=frage,
                kanal=kanal,
                antwort=antwort,
            ))
            embeddings.append(emb_rows[faq_id])

        if embeddings:
            self.embedding_matrix = np.stack(embeddings)
        else:
            dim = self.model.get_sentence_embedding_dimension() or 1024
            self.embedding_matrix = np.empty((0, dim))

    def search(
        self,
        query: str,
        top_k: int = 5,
        channel: str | None = None,
    ) -> list[SearchResult]:
        """Search for FAQs matching the query.

        Args:
            query: User's question
            top_k: Number of results to return
            channel: Optional channel filter (e.g. "telefonisch")

        Returns:
            List of SearchResult sorted by similarity score.
            Results with negative cosine similarity are excluded.
        """
        query_emb = self.model.encode(query, convert_to_numpy=True)

        if channel:
            mask = np.array([e.kanal == channel for e in self.entries])
            filtered_embeddings = self.embedding_matrix[mask]
            filtered_entries = [e for e, m in zip(self.entries, mask) if m]
        else:
            filtered_embeddings = self.embedding_matrix
            filtered_entries = self.entries

        scores = util.cos_sim(query_emb, filtered_embeddings)[0].cpu().numpy()
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] < 0:
                break
            results.append(SearchResult(
                entry=filtered_entries[int(idx)],
                score=float(scores[idx]),
            ))

        return results
