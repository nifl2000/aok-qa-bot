import json
from qa_bot.retriever import Retriever
from eval_set import EVAL_SET

print("Loading retriever...")
retriever = Retriever()
print(f"Loaded {len(retriever.entries)} entries")

results = []

for i, entry in enumerate(EVAL_SET):
    paraphrase = entry["paraphrase"]
    original_id = entry["original_id"]

    search_results = retriever.search(paraphrase, top_k=10)

    rank = None
    correct_score = None
    for pos, sr in enumerate(search_results, 1):
        if sr.entry.id == original_id:
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

    all_scores = [(sr.entry.id, sr.score, sr.entry.frage) for sr in search_results]

    result = {
        "index": i + 1,
        "original_id": original_id,
        "original_frage": entry["original_frage"],
        "paraphrase": paraphrase,
        "hauptthema": entry["hauptthema"],
        "rank": rank,
        "correct_score": correct_score,
        "top1": top1,
        "all_top10": all_scores,
    }
    results.append(result)

    status = f"RANK={rank}" if rank else "NOT FOUND"
    print(f"[{i+1:2d}] ID={original_id:5d} | {status} | score={correct_score:.4f}" if correct_score else f"[{i+1:2d}] ID={original_id:5d} | {status}")

# Save results
with open("eval_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\nResults saved to eval_results.json")
