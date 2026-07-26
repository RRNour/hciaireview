#!/usr/bin/env python3
"""
Script 05 — Classify AI Type
==============================
Assigns each paper a dominant AI type using the priority order
in config/ai_terms.yaml. Priority 1 (agentic_ai) wins over priority 8 (classical_ml).

Input:  data/normalized/filtered_records.jsonl
Output: data/normalized/classified_records.jsonl
"""
import argparse, json, os
import yaml

def classify_ai_type(text, type_terms, priority_order):
    text_lower = text.lower()
    matched = {}
    for ai_type, terms in type_terms.items():
        if any(t.lower() in text_lower for t in terms):
            matched[ai_type] = priority_order.get(ai_type, 99)
    if not matched:
        return "unclassified", False, False, False
    dominant = min(matched, key=lambda k: matched[k])
    is_genai = dominant in ("generative_ai", "llm", "copilot")
    is_llm = dominant == "llm"
    is_agentic = dominant == "agentic_ai"
    return dominant, is_genai, is_llm, is_agentic

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/config.yaml")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)
    with open("config/ai_terms.yaml") as f:
        ai_cfg = yaml.safe_load(f)

    type_terms = ai_cfg["ai_type_terms"]
    priority = ai_cfg["ai_type_priority"]

    in_path = os.path.join(cfg["paths"]["normalized"], "filtered_records.jsonl")
    out_dir = cfg["paths"]["normalized"]

    records = []
    with open(in_path, encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line.strip()))

    for rec in records:
        text = f"{rec.get('title','')} {rec.get('abstract','')} {' '.join(rec.get('concepts',[]))}"
        ai_type, genai, llm, agentic = classify_ai_type(text, type_terms, priority)
        rec["ai_type"] = ai_type
        rec["genai_flag"] = genai
        rec["llm_flag"] = llm
        rec["agentic_flag"] = agentic

    out_path = os.path.join(out_dir, "classified_records.jsonl")
    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    from collections import Counter
    type_dist = Counter(r["ai_type"] for r in records)
    print(f"AI type classification complete: {len(records)} records")
    for t, c in sorted(type_dist.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}")

if __name__ == "__main__":
    main()
