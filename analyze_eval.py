import json

with open("eval_results.json", "r", encoding="utf-8") as f:
    results = json.load(f)

total = len(results)
found = [r for r in results if r["rank"] is not None]
not_found = [r for r in results if r["rank"] is None]

recall_at_1 = sum(1 for r in results if r["rank"] is not None and r["rank"] <= 1) / total
recall_at_3 = sum(1 for r in results if r["rank"] is not None and r["rank"] <= 3) / total
recall_at_5 = sum(1 for r in results if r["rank"] is not None and r["rank"] <= 5) / total
recall_at_10 = sum(1 for r in results if r["rank"] is not None and r["rank"] <= 10) / total

rr_values = []
for r in results:
    if r["rank"] is not None:
        rr_values.append(1.0 / r["rank"])
    else:
        rr_values.append(0.0)
mrr = sum(rr_values) / len(rr_values)

print(f"Total: {total}")
print(f"Found in top 10: {len(found)}/{total} ({len(found)/total*100:.1f}%)")
print(f"Not found: {len(not_found)}/{total} ({len(not_found)/total*100:.1f}%)")
print()
print(f"Recall@1:  {recall_at_1*100:.1f}%")
print(f"Recall@3:  {recall_at_3*100:.1f}%")
print(f"Recall@5:  {recall_at_5*100:.1f}%")
print(f"Recall@10: {recall_at_10*100:.1f}%")
print(f"MRR:       {mrr:.4f}")
print()

# Score analysis
correct_scores = [r["correct_score"] for r in found]
print(f"Correct match scores: min={min(correct_scores):.4f}, max={max(correct_scores):.4f}, mean={sum(correct_scores)/len(correct_scores):.4f}")

# Score analysis for top-1 when wrong
wrong_top1_scores = []
for r in results:
    if r["top1"] and r["rank"] != 1:
        wrong_top1_scores.append(r["top1"]["score"])
    elif r["top1"] and r["rank"] == 1:
        pass  # correct, skip

print(f"Top-1 scores (when correct is not #1): {len(wrong_top1_scores)} cases")
if wrong_top1_scores:
    print(f"  min={min(wrong_top1_scores):.4f}, max={max(wrong_top1_scores):.4f}, mean={sum(wrong_top1_scores)/len(wrong_top1_scores):.4f}")

# Not found IDs
print()
print("Not found IDs:", [r["original_id"] for r in not_found])

# Per-topic analysis
from collections import defaultdict
topic_results = defaultdict(lambda: {"total": 0, "found": 0, "ranks": []})
for r in results:
    topic = r["hauptthema"]
    topic_results[topic]["total"] += 1
    if r["rank"] is not None:
        topic_results[topic]["found"] += 1
        topic_results[topic]["ranks"].append(r["rank"])

print()
print("Per-topic breakdown:")
for topic, data in sorted(topic_results.items()):
    rate = data["found"] / data["total"] * 100
    avg_rank = sum(data["ranks"]) / len(data["ranks"]) if data["ranks"] else "N/A"
    print(f"  {topic}: {data['found']}/{data['total']} ({rate:.0f}%), avg_rank={avg_rank}")
