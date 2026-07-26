#!/usr/bin/env python3
"""
Script 08 — Detect Evaluation Signals (ESRS Scoring)
======================================================
Scores each paper on the Evaluation Signal Robustness Score (ESRS, 0-8).
One point per dimension per config/evaluation_terms.yaml.

Input:  data/normalized/control_scored_records.jsonl
Output: data/normalized/eval_scored_records.jsonl
"""
import argparse, json, os
import yaml

def score_esrs(text, dimensions):
    text_lower = text.lower()
    score = 0
    matched = []
    for dim_str, dim_data in dimensions.items():
        terms = dim_data.get("trigger_terms", [])
        if any(str(t).lower() in text_lower for t in terms):
            score += 1
            matched.append(int(dim_str))
    return score, matched

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/config.yaml")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)
    with open("config/evaluation_terms.yaml") as f:
        eval_cfg = yaml.safe_load(f)

    dimensions = eval_cfg["esrs_dimensions"]

    in_path = os.path.join(cfg["paths"]["normalized"], "control_scored_records.jsonl")
    out_dir = cfg["paths"]["normalized"]

    records = []
    with open(in_path, encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line.strip()))

    for rec in records:
        text = f"{rec.get('title','')} {rec.get('abstract_filtered', rec.get('abstract',''))}"
        esrs, dims = score_esrs(text, dimensions)
        rec["esrs"] = esrs
        rec["esrs_dimensions_matched"] = dims

    out_path = os.path.join(out_dir, "eval_scored_records.jsonl")
    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    import statistics
    scores = [r["esrs"] for r in records]
    print(f"Evaluation scoring complete: {len(records)} records")
    print(f"  Mean ESRS: {statistics.mean(scores):.2f}, Median: {statistics.median(scores):.1f}")

if __name__ == "__main__":
    main()
