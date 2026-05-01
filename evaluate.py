import sqlite3
import json
import time
import sys
import os
import re
from eval_set import EVAL_SET
from qa_bot.retriever import Retriever
from qa_bot.text_utils import clean_answer

def normalize(text):
    """Normalize text for matching: lower case, replace umlauts, remove non-alphanumeric."""
    if not text:
        return ""
    text = text.lower()
    mapping = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}
    for k, v in mapping.items():
        text = text.replace(k, v)
    # Remove everything except alphanumeric
    text = re.sub(r'[^a-z0-9]', '', text)
    return text

def run_evaluation(use_llm=False):
    if use_llm and not os.environ.get("LLM_API_KEY"):
        print("Error: LLM_API_KEY environment variable not set.")
        return

    print(f"Initializing Retriever (LLM Rerank: {use_llm})...")
    retriever = Retriever()
    
    # Map (norm_frage, norm_hauptthema) -> faq_id
    print("Building lookup map...")
    lookup = {}
    for entry in retriever.entries:
        # We store multiple keys if normalization collapses them
        norm_q = normalize(entry.frage)
        norm_h = normalize(entry.hauptthema)
        key = (norm_q, norm_h)
        lookup[key] = entry.id

    total = len(EVAL_SET)
    print(f"Starting evaluation on {total} queries...")
    
    hits_at_1 = 0
    hits_at_3 = 0
    mrr_sum = 0
    skipped = 0
    
    start_time = time.time()
    
    for i, eval_item in enumerate(EVAL_SET):
        query = eval_item["paraphrase"]
        target_key = (normalize(eval_item["original_frage"]), normalize(eval_item["hauptthema"]))
        target_id = lookup.get(target_key)
        
        if target_id is None:
            # Fallback: try matching just the question if topic normalization differed
            norm_q = target_key[0]
            possible_ids = [eid for (q, h), eid in lookup.items() if q == norm_q]
            if len(possible_ids) == 1:
                target_id = possible_ids[0]
            else:
                print(f"Warning: Target not found in DB: {eval_item['original_frage']} | {eval_item['hauptthema']}")
                skipped += 1
                continue
            
        # Search (using new defaults, which is LLM rerank if use_llm is passed, 
        # but the script's use_llm flag should control it explicitly for metrics)
        try:
            search_results = retriever.search(
                query, 
                top_k=20, 
                llm_rerank=use_llm
            )
        except Exception as e:
            print(f"Error searching for '{query}': {e}")
            continue
        
        # Calculate metrics
        rank = 0
        for idx, res in enumerate(search_results, 1):
            if res.entry.id == target_id:
                rank = idx
                break
        
        if rank == 1:
            hits_at_1 += 1
        if 1 <= rank <= 3:
            hits_at_3 += 1
        if rank > 0:
            mrr_sum += 1.0 / rank
            
        if (i + 1) % 5 == 0:
            print(f"Processed {i+1}/{total}...")

    duration = time.time() - start_time
    effective_total = total - skipped
    
    recall_at_1 = hits_at_1 / effective_total if effective_total > 0 else 0
    recall_at_3 = hits_at_3 / effective_total if effective_total > 0 else 0
    mrr = mrr_sum / effective_total if effective_total > 0 else 0
    
    mode_str = "LLM Reranking" if use_llm else "Embedding-only"
    print("\n" + "="*40)
    print(f"EVALUATION RESULTS ({mode_str})")
    print("="*40)
    print(f"Queries total:     {total}")
    print(f"Matched in DB:     {effective_total}")
    print(f"Recall@1:          {recall_at_1:.2%}")
    print(f"Recall@3:          {recall_at_3:.2%}")
    print(f"MRR:               {mrr:.3f}")
    print(f"Duration total:    {duration:.2f}s")
    print(f"Avg time/query:    {duration/total:.3f}s")
    print("="*40)

if __name__ == "__main__":
    use_llm = "--llm" in sys.argv
    run_evaluation(use_llm=use_llm)
