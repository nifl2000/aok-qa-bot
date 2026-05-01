import json

with open("eval_results.json", "r", encoding="utf-8") as f:
    results = json.load(f)

not_found = [r for r in results if r["rank"] is None]

for r in not_found:
    print(f"--- ID={r['original_id']} ---")
    print(f"Original: {r['original_frage']}")
    print(f"Paraphrase: {r['paraphrase']}")
    print(f"Topic: {r['hauptthema']}")
    print(f"Top-1 returned: ID={r['top1']['id']} score={r['top1']['score']:.4f}")
    print(f"  Top-1 frage: {r['top1']['frage']}")
    print(f"Top-10 results:")
    for idx, (sid, sscore, sfrase) in enumerate(r['all_top10'], 1):
        print(f"  {idx}. ID={sid} score={sscore:.4f} | {sfrase[:100]}")
    print()
