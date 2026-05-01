from __future__ import annotations

import json
import re
import sqlite3
import time

import httpx
import numpy as np
from sentence_transformers import CrossEncoder, SentenceTransformer, util

from qa_bot.config import llm_api_key as _get_api_key
from qa_bot.models import (
    Answer,
    FAQEntry,
    SearchResult,
    MODEL_NAME,
    DEFAULT_DB_PATH,
    LLM_RERANK_MODEL,
    LLM_RERANK_BASE_URL,
)


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

    def __init__(
        self,
        db_path: str = DEFAULT_DB_PATH,
        model_name: str = MODEL_NAME,
        llm_api_key: str | None = None,
        llm_base_url: str = LLM_RERANK_BASE_URL,
        llm_model: str = LLM_RERANK_MODEL,
    ):
        self.db_path = db_path
        self.model = SentenceTransformer(model_name)
        self._rerank_model: CrossEncoder | None = None
        self.llm_api_key = llm_api_key or _get_api_key()
        self.llm_base_url = llm_base_url
        self.llm_model = llm_model
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

    CROSS_ENCODER_MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"

    _LLM_RERANK_PROMPT = """Du bewertest die semantische Übereinstimmung zwischen einer Nutzerfrage und FAQ-Einträgen.

Aufgabe: Bewerte jeden der {n} FAQ-Einträge von 0 bis 10.
10 = perfekte Übereinstimmung (die FAQ-Frage ist eine Paraphrase der Nutzerfrage)
0 = keine inhaltliche Übereinstimmung

Antworte NUR mit einem JSON-Objekt mit einem "scores"-Array der Länge {n}, wobei der i-te Eintrag die Bewertung des i-ten FAQ-Eintrags ist.
Beispielantwort: {{"scores": [8, 3, 1, 0, 7, 2]}}

Nutzerfrage: {query}

FAQ-Einträge:
{entries}
"""

    def _llm_rerank(
        self,
        query: str,
        candidates: list[tuple[int, str, float]],
    ) -> list[tuple[int, float]]:
        """Rerank candidates using LLM scoring.

        Sends query + candidate FAQ texts to the LLM, parses JSON scores.

        Args:
            query: User's question
            candidates: List of (faq_id, frage_text, original_score) tuples

        Returns:
            List of (faq_id, llm_score) sorted by LLM score descending.
        """
        if not candidates or not self.llm_api_key:
            return []

        # Build candidate list for the prompt
        entries_text = "\n".join(
            f"[{cid}] {text}" for cid, text, _ in candidates
        )
        prompt = self._LLM_RERANK_PROMPT.format(
            query=query, entries=entries_text, n=len(candidates)
        )

        body = {
            "model": self.llm_model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": 0,
            "max_tokens": 2000,
        }

        # Retry up to 2 times on timeout
        for attempt in range(3):
            try:
                response = httpx.post(
                    f"{self.llm_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.llm_api_key}",
                        "Content-Type": "application/json",
                    },
                    json=body,
                    timeout=180,
                )
                break
            except httpx.ReadTimeout:
                if attempt == 2:
                    raise
                time.sleep(2 * (attempt + 1))

        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()

        # Handle code block wrapping
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("\n", 1)[0]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        result = json.loads(content)

        # Handle both {"scores": [...]} and direct array formats
        if isinstance(result, dict) and "scores" in result:
            scores = result["scores"]
        elif isinstance(result, dict) and "ranking" in result:
            scores = [item["score"] for item in result["ranking"]]
        elif isinstance(result, list):
            scores = result
        else:
            raise ValueError(f"Unexpected LLM response format: {content[:200]}")

        ranked = []
        for i, (faq_id, _, _) in enumerate(candidates):
            score = scores[i] if i < len(scores) else 0
            ranked.append((faq_id, float(score)))

        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked

    def _rerank(
        self,
        query: str,
        candidates: list[tuple[int, str, float]],
    ) -> list[tuple[int, float]]:
        """Rerank candidates using Cross-Encoder.

        Args:
            query: User's question
            candidates: List of (faq_id, frage_text, original_score) tuples

        Returns:
            List of (faq_id, rerank_score) sorted by cross-encoder score descending.
        """
        if not candidates:
            return []

        if self._rerank_model is None:
            self._rerank_model = CrossEncoder(self.CROSS_ENCODER_MODEL)

        pairs = [(query, text) for _, text, _ in candidates]
        scores = self._rerank_model.predict(pairs)

        ranked = [(faq_id, float(score)) for (faq_id, _, _), score in zip(candidates, scores)]
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked

    def search(
        self,
        query: str,
        top_k: int = 5,
        channel: str | None = None,
        topic: str | None = None,
        hybrid: bool = False,
        rerank: bool = False,
        rerank_top_k: int = 20,
        llm_rerank: bool = False,
        llm_rerank_top_k: int = 20,
    ) -> list[SearchResult]:
        """Search for FAQs matching the query.

        Args:
            query: User's question
            top_k: Number of results to return
            channel: Optional channel filter (e.g. "telefonisch")
            topic: Optional topic filter (e.g. "Mutterschaftsgeld")
            hybrid: If True, combine BM25 + Embedding with RRF.
            rerank: If True, rerank top-k embedding results with Cross-Encoder.
            rerank_top_k: Number of candidates to fetch before reranking.
            llm_rerank: If True, rerank top-k candidates using LLM scoring.
            llm_rerank_top_k: Number of candidates to fetch before LLM reranking.

        Returns:
            List of SearchResult sorted by combined score.
        """
        if llm_rerank:
            # Stage 1: Get candidates via embedding search
            embed_results = self._embedding_search(query, llm_rerank_top_k, topic=topic, channel=channel)
            candidates = []
            for doc_id, score in embed_results:
                entry = self._get_entry(doc_id)
                if entry:
                    candidates.append((doc_id, entry.frage, score))

            # Stage 2: Rerank with LLM
            reranked = self._llm_rerank(query, candidates)

            # Build results
            results = []
            for doc_id, rerank_score in reranked[:top_k]:
                entry = self._get_entry(doc_id)
                if entry is None:
                    continue
                results.append(SearchResult(
                    entry=entry,
                    score=rerank_score,
                    rerank_score=rerank_score,
                ))
            return results
        elif rerank:
            # Stage 1: Get candidates via embedding search
            embed_results = self._embedding_search(query, rerank_top_k, topic=topic, channel=channel)
            candidates = []
            for doc_id, score in embed_results:
                entry = self._get_entry(doc_id)
                if entry:
                    candidates.append((doc_id, entry.frage, score))

            # Stage 2: Rerank with Cross-Encoder
            reranked = self._rerank(query, candidates)

            # Build results
            results = []
            for doc_id, rerank_score in reranked[:top_k]:
                entry = self._get_entry(doc_id)
                if entry is None:
                    continue
                results.append(SearchResult(
                    entry=entry,
                    score=rerank_score,
                    rerank_score=rerank_score,
                ))
            return results
        elif hybrid:
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
