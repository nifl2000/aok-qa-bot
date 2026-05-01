#!/usr/bin/env python3
"""Evaluate the retriever against the 50-question eval set.

Compares embedding-only, cross-encoder reranking, and LLM reranking.
Uses id_mapping.json to translate old eval_set IDs to new deduplicated IDs.
Reports Recall@K and MRR metrics.
"""

import json
import os
from eval_set import EVAL_SET
from qa_bot.retriever import Retriever

# Load ID mapping
with open("id_mapping.json") as f:
    ID_MAP = json.load(f)


def evaluate(
    retriever: Retriever,
    rerank: bool = False,
    rerank_top_k: int = 20,
    llm_rerank: bool = False,
    llm_rerank_top_k: int = 20,
) -> tuple[list[dict], dict]:
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
            results.append({
                "original_id": original_id,
                "paraphrase": paraphrase,
                "rank": None,
                "error": "ID not mapped",
            })
            continue

        search_results = retriever.search(
            paraphrase, top_k=10, rerank=rerank, rerank_top_k=rerank_top_k,
            llm_rerank=llm_rerank, llm_rerank_top_k=llm_rerank_top_k,
        )

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
            "paraphrase": paraphrase,
            "hauptthema": item["hauptthema"],
            "rank": rank,
            "correct_score": correct_score,
            "top1": top1,
        }
        if (rerank or llm_rerank) and rank:
            sr = search_results[rank - 1]
            result["rerank_score"] = sr.rerank_score

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
    retriever = Retriever(
        llm_api_key=os.environ.get("LLM_API_KEY"),
    )
    print(f"Loaded {len(retriever.entries)} deduplicated entries\n")

    # Embedding-only
    print("=" * 70)
    print("EMBEDDING-ONLY (baseline)")
    print("=" * 70)
    embed_results, embed_metrics = evaluate(retriever)
    print(f"Recall@1:  {embed_metrics['recall_at_1']*100:.1f}%")
    print(f"Recall@3:  {embed_metrics['recall_at_3']*100:.1f}%")
    print(f"Recall@5:  {embed_metrics['recall_at_5']*100:.1f}%")
    print(f"Recall@10: {embed_metrics['recall_at_10']*100:.1f}%")
    print(f"MRR:       {embed_metrics['mrr']:.4f}")
    print(f"Not found: {embed_metrics['not_found']*100:.1f}%")

    # LLM Reranking (reuse same retriever, just change model)
    llm_model = "kimi-k2.5"
    print()
    print("=" * 70)
    print(f"LLM RERANKING (Embedding top-20 + {llm_model})")
    print("=" * 70)
    retriever.llm_model = llm_model
    retriever.llm_api_key = os.environ.get("LLM_API_KEY")
    llm_results, llm_metrics = evaluate(
        retriever, llm_rerank=True, llm_rerank_top_k=20
    )
    print(f"Recall@1:  {llm_metrics['recall_at_1']*100:.1f}%")
    print(f"Recall@3:  {llm_metrics['recall_at_3']*100:.1f}%")
    print(f"Recall@5:  {llm_metrics['recall_at_5']*100:.1f}%")
    print(f"Recall@10: {llm_metrics['recall_at_10']*100:.1f}%")
    print(f"MRR:       {llm_metrics['mrr']:.4f}")
    print(f"Not found: {llm_metrics['not_found']*100:.1f}%")

    # Diff
    print()
    print("=" * 70)
    print(f"DIFF: LLM Rerank vs Embedding-only")
    print("=" * 70)
    improved = 0
    degraded = 0
    for i, (er, lr) in enumerate(zip(embed_results, llm_results)):
        r1 = er.get("rank")
        r2 = lr.get("rank")
        if r1 != r2:
            if r2 is not None and (r1 is None or r2 < r1):
                status = "BETTER"
                improved += 1
            elif r1 is not None and (r2 is None or r2 > r1):
                status = "WORSE"
                degraded += 1
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
            print(f"  [{i+1:2d}] ID={lr['original_id']:5d} {status:6s} {detail:10s} | {lr['paraphrase'][:60]}")

    print(f"\n  Summary: {improved} improved, {degraded} degraded")

    # Comparison table
    print()
    print("=" * 70)
    print("COMPARISON")
    print("=" * 70)
    print(f"{'Metric':<12} {'Embedding':>10} {'LLM Rerank':>12} {'Change':>10}")
    print("-" * 50)
    for key, label in [("recall_at_1", "Recall@1"), ("recall_at_3", "Recall@3"),
                        ("recall_at_5", "Recall@5"), ("recall_at_10", "Recall@10"),
                        ("mrr", "MRR"), ("not_found", "Not found")]:
        ev = embed_metrics[key] * 100
        lv = llm_metrics[key] * 100
        chg = "+" if lv >= ev else ""
        print(f"{label:<12} {ev:>9.1f}% {lv:>11.1f}% {chg}{lv-ev:>+.1f}pp")

    # Conclusion
    print()
    print("=" * 70)
    print("CONCLUSION")
    print("=" * 70)
    if llm_metrics["recall_at_1"] > embed_metrics["recall_at_1"]:
        print(f"LLM reranking ({llm_model}) improves Recall@1 from")
        print(f"{embed_metrics['recall_at_1']*100:.1f}% to {llm_metrics['recall_at_1']*100:.1f}%")
        print(f"({'+' if llm_metrics['recall_at_1'] > embed_metrics['recall_at_1'] else ''}{(llm_metrics['recall_at_1'] - embed_metrics['recall_at_1'])*100:.1f}pp).")
        if llm_metrics["recall_at_1"] >= 0.80:
            print(f"Recommendation: Use LLM reranking as default.")
        else:
            print(f"Recommendation: Consider LLM reranking for production.")
    else:
        print(f"LLM reranking ({llm_model}) does not improve over embedding-only.")
        print(f"Embedding-only remains recommended.")

    # Save results
    with open("eval_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "embedding_only": {"metrics": embed_metrics, "results": embed_results},
            "llm_rerank": {"metrics": llm_metrics, "results": llm_results},
            "llm_model": llm_model,
            "baseline_recall_1": 0.18,
            "baseline_recall_3": 0.52,
            "baseline_recall_5": 0.72,
            "baseline_recall_10": 0.80,
            "baseline_mrr": 0.3740,
            "conclusion": (
                f"LLM reranking ({llm_model}): {llm_metrics['recall_at_1']*100:.1f}% R@1"
            ),
        }, f, ensure_ascii=False, indent=2)

    print(f"\nResults saved to eval_results.json")


if __name__ == "__main__":
    main()
