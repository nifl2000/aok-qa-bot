#!/usr/bin/env python3
"""Evaluate the hybrid retriever against the 50-question eval set.

Compares hybrid (BM25+Embedding RRF) vs embedding-only search.
Uses id_mapping.json to translate old eval_set IDs to new deduplicated IDs.
Reports Recall@K and MRR metrics.
"""

import json
from eval_set import EVAL_SET
from qa_bot.retriever import Retriever

# Load ID mapping
with open("id_mapping.json") as f:
    ID_MAP = json.load(f)


def evaluate(retriever: Retriever, hybrid: bool = True) -> tuple[list[dict], dict]:
    """Run evaluation and return per-item results and aggregate metrics."""
    results = []
    k_values = [1, 3, 5, 10]
    recalls = {k: 0 for k in k_values}
    mrr_sum = 0.0

    for item in EVAL_SET:
        paraphrase = item["paraphrase"]
        original_id = item["original_id"]
        new_id = ID_MAP.get(str(original_id))

        if new_id is None:
            result = {
                "original_id": original_id,
                "original_frage": item["original_frage"],
                "paraphrase": paraphrase,
                "hauptthema": item["hauptthema"],
                "rank": None,
                "correct_score": None,
                "error": "ID not mapped",
            }
            results.append(result)
            continue

        search_results = retriever.search(paraphrase, top_k=10, hybrid=hybrid)

        rank = None
        correct_score = None
        for pos, sr in enumerate(search_results, 1):
            if sr.entry.id == new_id:
                rank = pos
                correct_score = sr.score
                break

        top1 = None
        if search_results:
            top1 = {
                "id": search_results[0].entry.id,
                "frage": search_results[0].entry.frage,
                "score": search_results[0].score,
            }

        for k in k_values:
            if rank is not None and rank <= k:
                recalls[k] += 1

        if rank is not None:
            mrr_sum += 1.0 / rank

        result = {
            "original_id": original_id,
            "new_id": new_id,
            "original_frage": item["original_frage"],
            "paraphrase": paraphrase,
            "hauptthema": item["hauptthema"],
            "rank": rank,
            "correct_score": correct_score,
            "top1": top1,
        }
        if hybrid and rank:
            sr = search_results[rank - 1]
            result["bm25_score"] = sr.bm25_score
            result["embed_score"] = sr.embed_score
            result["rrf_score"] = sr.rrf_score

        results.append(result)

    n = len(EVAL_SET)
    metrics = {
        "recall_at_1": recalls[1] / n,
        "recall_at_3": recalls[3] / n,
        "recall_at_5": recalls[5] / n,
        "recall_at_10": recalls[10] / n,
        "mrr": mrr_sum / n,
        "not_found": sum(1 for r in results if r.get("rank") is None) / n,
    }

    return results, metrics


def main():
    print("Loading retriever...")
    retriever = Retriever()
    print(f"Loaded {len(retriever.entries)} deduplicated entries\n")

    print("=" * 60)
    print("EMBEDDING-ONLY (dedup index)")
    print("=" * 60)
    embed_results, embed_metrics = evaluate(retriever, hybrid=False)
    print(f"Recall@1:  {embed_metrics['recall_at_1']*100:.1f}%")
    print(f"Recall@3:  {embed_metrics['recall_at_3']*100:.1f}%")
    print(f"Recall@5:  {embed_metrics['recall_at_5']*100:.1f}%")
    print(f"Recall@10: {embed_metrics['recall_at_10']*100:.1f}%")
    print(f"MRR:       {embed_metrics['mrr']:.4f}")
    print(f"Not found: {embed_metrics['not_found']*100:.1f}%")

    print()
    print("=" * 60)
    print("HYBRID (BM25 + Embedding + RRF)")
    print("=" * 60)
    hybrid_results, hybrid_metrics = evaluate(retriever, hybrid=True)
    print(f"Recall@1:  {hybrid_metrics['recall_at_1']*100:.1f}%")
    print(f"Recall@3:  {hybrid_metrics['recall_at_3']*100:.1f}%")
    print(f"Recall@5:  {hybrid_metrics['recall_at_5']*100:.1f}%")
    print(f"Recall@10: {hybrid_metrics['recall_at_10']*100:.1f}%")
    print(f"MRR:       {hybrid_metrics['mrr']:.4f}")
    print(f"Not found: {hybrid_metrics['not_found']*100:.1f}%")

    print()
    print("=" * 60)
    print("PREVIOUS BASELINE (4992-entry index, from quality_assessment.md)")
    print("=" * 60)
    print(f"Recall@1:  18.0%")
    print(f"Recall@3:  52.0%")
    print(f"Recall@5:  72.0%")
    print(f"Recall@10: 80.0%")
    print(f"MRR:       0.3740")
    print(f"Not found: 20.0%")

    # Diff
    print()
    print("=" * 60)
    print("DIFF: Hybrid vs Embedding-only")
    print("=" * 60)
    for i, (er, hr) in enumerate(zip(embed_results, hybrid_results)):
        r1 = er.get("rank")
        r2 = hr.get("rank")
        if r1 != r2:
            if r2 is not None and (r1 is None or r2 < r1):
                status = "BETTER"
            elif r1 is not None and (r2 is None or r2 > r1):
                status = "WORSE"
            else:
                status = "CHANGE"
            if r1 is None and r2 is not None:
                detail = f"NF -> R{r2}"
            elif r1 is not None and r2 is None:
                detail = f"R{r1} -> NF"
            elif r1 is not None and r2 is not None:
                detail = f"R{r1} -> R{r2}"
            else:
                detail = "NF -> NF"
            print(f"  [{i+1:2d}] ID={hr['original_id']:5d} {status:6s} {detail:10s} | {hr['paraphrase'][:60]}")

    # Save results
    with open("eval_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "embedding_only": {"metrics": embed_metrics, "results": embed_results},
            "hybrid": {"metrics": hybrid_metrics, "results": hybrid_results},
            "baseline_recall_1": 0.18,
            "baseline_recall_3": 0.52,
            "baseline_recall_5": 0.72,
            "baseline_recall_10": 0.80,
            "baseline_mrr": 0.3740,
        }, f, ensure_ascii=False, indent=2)

    print(f"\nResults saved to eval_results.json")


if __name__ == "__main__":
    main()
