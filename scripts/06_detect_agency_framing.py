#!/usr/bin/env python3
"""
Script 06 — Detect Agency Framing (TAFS Scoring)
==================================================
Scores each paper on the Textual Agency Framing Score (TAFS, 0-5)
using the trigger terms in config/agency_terms.yaml.
Assigns the highest matching level. Sets the high_agency binary flag
at TAFS >= config.scoring.tafs_high_agency_threshold (default: 3).

Scoring logic: assign the highest TAFS level for which any trigger
term is found in title + filtered abstract. If multiple levels match,
the maximum wins (e.g., if both level-2 and level-4 terms appear,
TAFS = 4).

Input:  data/normalized/classified_records.jsonl
Output: data/normalized/agency_scored_records.jsonl
"""
import argparse, json, os
import yaml

def score_tafs(text, level_terms):
    text_lower = text.lower()
    max_level = 0
    matched_terms = []
    for level_str, level_data in level_terms.items():
        level = int(level_str)
        terms = level_data.get("trigger_terms", [])
        for term in terms:
            if str(term).lower() in text_lower:
                if level > max_level:
                    max_level = level
                    matched_terms = [str(term)]
                elif level == max_level:
                    matched_terms.append(str(term))
                break
    return max_level, matched_terms

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/config.yaml")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)
    with open("config/agency_terms.yaml") as f:
        agency_cfg = yaml.safe_load(f)

    level_terms = agency_cfg["tafs_levels"]
    threshold = cfg["scoring"]["tafs_high_agency_threshold"]

    in_path = os.path.join(cfg["paths"]["normalized"], "classified_records.jsonl")
    out_dir = cfg["paths"]["normalized"]

    records = []
    with open(in_path, encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line.strip()))

    for rec in records:
        text = f"{rec.get('title','')} {rec.get('abstract_filtered', rec.get('abstract',''))}"
        tafs, terms = score_tafs(text, level_terms)
        rec["tafs"] = tafs
        rec["tafs_trigger_terms"] = terms
        rec["high_agency"] = tafs >= threshold

    out_path = os.path.join(out_dir, "agency_scored_records.jsonl")
    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    ha_count = sum(1 for r in records if r["high_agency"])
    print(f"Agency scoring complete: {len(records)} records")
    print(f"  High-agency (TAFS >= {threshold}): {ha_count} ({100*ha_count/len(records):.1f}%)")
    from collections import Counter
    dist = Counter(r["tafs"] for r in records)
    for level in sorted(dist):
        print(f"  TAFS {level}: {dist[level]}")

if __name__ == "__main__":
    main()
