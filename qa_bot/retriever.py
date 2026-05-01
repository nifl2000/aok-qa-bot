from __future__ import annotations

import json
import re
import sqlite3

import numpy as np
from sentence_transformers import SentenceTransformer, util

from qa_bot.models import Answer, FAQEntry, SearchResult, MODEL_NAME, DEFAULT_DB_PATH


def _fts_escape(term: str) -> str:
    """Escape a term for safe use in FTS5 MATCH query."""
    # Wrap in double quotes for phrase matching, escape internal quotes
    return '"' + term.replace('"', '""') + '"'


# Words to exclude from BM25 queries — too common to be discriminative
_BM25_STOP_WORDS = frozenset({
    "muss", "kann", "will", "bin", "bei", "was", "wie", "wird",
    "auch", "noch", "nur", "oder", "aber", "nicht", "nach",
    "dann", "doch", "hier", "sehr", "so", "viel", "man",
    "werden", "ist", "das", "den", "dem", "der", "die",
    "und", "ein", "eine", "einem", "einen", "einer",
    "für", "von", "mit", "wenn", "ich", "mein", "meine",
    "mir", "sich", "über", "zum", "zur",
})


class Retriever:
    """Hybrid search over FAQs combining BM25 (FTS5) and embedding similarity."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH, model_name: str = MODEL_NAME):
        self.db_path = db_path
        self.model = SentenceTransformer(model_name)
        self._load_embeddings()

    def _load_embeddings(self) -> None:
        """Load all FAQ entries and embeddings from SQLite."""
        with sqlite3.connect(self.db_path) as db:
            cur = db.cursor()
            cur.execute("SELECT id, hauptthema, subthema, frage, answers_json FROM faqs")
            rows = cur.fetchall()

            cur.execute("SELECT faq_id, embedding FROM faq_embeddings")
            emb_rows = {row[0]: np.frombuffer(row[1], dtype=np.float32) for row in cur.fetchall()}

        self.entries: list[FAQEntry] = []
        self.embedding_matrix: np.ndarray
        embeddings = []

        for row in rows:
            faq_id, hauptthema, subthema, frage, answers_json = row
            if faq_id not in emb_rows:
                continue
            answers_data = json.loads(answers_json)
            answers = [Answer(kanal=a["kanal"], antwort=a["antwort"]) for a in answers_data]
            self.entries.append(FAQEntry(
                id=faq_id,
                hauptthema=hauptthema,
                subthema=subthema,
                frage=frage,
                answers=answers,
            ))
            embeddings.append(emb_rows[faq_id])

        if embeddings:
            self.embedding_matrix = np.stack(embeddings)
        else:
            dim = self.model.get_sentence_embedding_dimension() or 1024
            self.embedding_matrix = np.empty((0, dim))

        # Map entry id -> index in entries list / embedding_matrix
        self._id_to_idx: dict[int, int] = {e.id: i for i, e in enumerate(self.entries)}

    def _bm25_search(
        self,
        query: str,
        top_k: int,
        topic: str | None = None,
    ) -> list[tuple[int, float]]:
        """BM25 search via FTS5. Returns list of (faq_id, score) sorted by rank.

        Score is derived from FTS5 rank (more negative = better).
        We convert to a positive score: score = -rank.
        """
        with sqlite3.connect(self.db_path) as db:
            cur = db.cursor()
            # Extract terms, filtering common words
            terms = re.findall(r"[a-zA-ZäöüÄÖÜß]{3,}", query.lower())
            terms = [t for t in terms if t not in _BM25_STOP_WORDS]
            if not terms:
                return []

            # Build FTS5 query with OR semantics
            fts_query = " OR ".join(_fts_escape(t) for t in terms)

            where = f"faqs_fts MATCH ?"
            params: list[str] = [fts_query]
            if topic:
                where += " AND hauptthema = ?"
                params.append(topic)

            cur.execute(
                f"SELECT rowid, rank FROM faqs_fts WHERE {where} ORDER BY rank LIMIT ?",
                (*params, top_k),
            )
            rows = cur.fetchall()

        # Convert rank (negative) to positive score
        results = []
        for rowid, rank in rows:
            score = -rank if rank != float('-inf') else 1e6
            results.append((int(rowid), float(score)))

        return results

    def _embedding_search(
        self,
        query: str,
        top_k: int,
        topic: str | None = None,
        channel: str | None = None,
    ) -> list[tuple[int, float]]:
        """Embedding search via cosine similarity. Returns (faq_id, score) sorted by score."""
        query_emb = self.model.encode(query, convert_to_numpy=True)

        # Build index mask
        mask = np.ones(len(self.entries), dtype=bool)
        if topic:
            topic_mask = np.array([e.hauptthema == topic for e in self.entries], dtype=bool)
            mask &= topic_mask
        if channel:
            channel_mask = np.array([
                any(a.kanal == channel for a in e.answers)
                for e in self.entries
            ], dtype=bool)
            mask &= channel_mask

        if not mask.any():
            return []

        filtered_embeddings = self.embedding_matrix[mask]
        filtered_ids = [e.id for e, m in zip(self.entries, mask) if m]

        scores = util.cos_sim(query_emb, filtered_embeddings)[0].cpu().numpy()
        # Get top_k indices within the filtered set
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] < 0:
                break
            results.append((filtered_ids[int(idx)], float(scores[idx])))

        return results

    @staticmethod
    def _rrf_merge(
        bm25_results: list[tuple[int, float]],
        embed_results: list[tuple[int, float]],
        top_k: int,
        k: int = 60,
    ) -> dict[int, float]:
        """Reciprocal Rank Fusion: merge two ranked lists.

        RRF_score(doc) = sum(1 / (k + rank_i)) for each ranking i
        rank is 1-based position in each list.
        """
        rrf_scores: dict[int, float] = {}

        for rank, (doc_id, _score) in enumerate(bm25_results, start=1):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1.0 / (k + rank)

        for rank, (doc_id, _score) in enumerate(embed_results, start=1):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1.0 / (k + rank)

        # Return top_k by RRF score
        sorted_ids = sorted(rrf_scores, key=rrf_scores.get, reverse=True)[:top_k]  # type: ignore[arg-type]
        return {doc_id: rrf_scores[doc_id] for doc_id in sorted_ids}

    def _get_entry(self, faq_id: int) -> FAQEntry | None:
        idx = self._id_to_idx.get(faq_id)
        if idx is None:
            return None
        return self.entries[idx]

    def search(
        self,
        query: str,
        top_k: int = 5,
        channel: str | None = None,
        topic: str | None = None,
        hybrid: bool = True,
    ) -> list[SearchResult]:
        """Search for FAQs matching the query.

        Args:
            query: User's question
            top_k: Number of results to return
            channel: Optional channel filter (e.g. "telefonisch")
            topic: Optional topic filter (e.g. "Mutterschaftsgeld")
            hybrid: If True, combine BM25 + Embedding with RRF.
                    If False, use embedding-only search.

        Returns:
            List of SearchResult sorted by combined score.
        """
        if hybrid:
            # Run both searches in parallel
            bm25_results = self._bm25_search(query, top_k * 10, topic=topic)
            embed_results = self._embedding_search(query, top_k * 10, topic=topic, channel=channel)

            # Merge with RRF
            rrf_scores = self._rrf_merge(bm25_results, embed_results, top_k)

            # Build lookup maps for individual scores
            bm25_map = {doc_id: score for doc_id, score in bm25_results}
            embed_map = {doc_id: score for doc_id, score in embed_results}

            results = []
            for doc_id, rrf_score in rrf_scores.items():
                entry = self._get_entry(doc_id)
                if entry is None:
                    continue
                results.append(SearchResult(
                    entry=entry,
                    score=rrf_score,
                    rrf_score=rrf_score,
                    bm25_score=bm25_map.get(doc_id, 0.0),
                    embed_score=embed_map.get(doc_id, 0.0),
                ))
            return results
        else:
            # Embedding-only search
            embed_results = self._embedding_search(query, top_k, topic=topic, channel=channel)
            results = []
            for doc_id, score in embed_results:
                entry = self._get_entry(doc_id)
                if entry is None:
                    continue
                results.append(SearchResult(
                    entry=entry,
                    score=score,
                    embed_score=score,
                ))
            return results
