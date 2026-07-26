"""
15_confidence_uncertainty_depth.py
====================================
Assign confidence scores to every record and flag uncertain
classifications for the sensitivity analyses.

Confidence scoring scheme (from plan §18):

Points:
  +3  exact phrase in title
  +2  exact phrase in abstract
  +2  exact phrase in keywords
  +3  exact phrase in system/evaluation section
  +2  multiple supporting phrases detected
  +2  specific mechanism detected (CSS=3)
  -1  vague term only (CSS=1)
  -2  ambiguous control context (polysemy near control)
  +2  L3 (section-level) evidence available
  -1  abstract word count <75

Score → Label:
  ≥6  high
  3-5 medium
  0-2 low

Inputs
------
data/final/final_index_table.jsonl
config/scoring_rules.yaml

Outputs
-------
data/final/confidence_scored_records.jsonl
outputs/tables/confidence_distribution.csv
outputs/reports/uncertainty_report.md
"""

import json, yaml, csv, re
from pathlib import Path
from collections import Counter


def load_config(path: str = "config/config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def load_scoring_cfg(path: str = "config/scoring_rules.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def compute_confidence(rec: dict, weights: dict) -> tuple[float, str]:
    score = 0.0

    if rec.get("_title_match", False):
        score += weights.get("title_match", 3)
    if rec.get("_abstract_match", False):
        score += weights.get("abstract_match", 2)
    if rec.get("_keyword_match", False):
        score += weights.get("keyword_match", 2)
    if rec.get("_section_match", False):
        score += weights.get("section_match", 3)
    if rec.get("_multi_phrase", False):
        score += weights.get("multi_phrase", 2)
    if rec.get("css_final", 0) == 3:
        score += weights.get("specific_mechanism", 2)
    elif rec.get("css_final", 0) == 1:
        score -= weights.get("vague_term_penalty", 1)
    if rec.get("_control_ambiguous", False):
        score -= weights.get("ambiguous_penalty", 2)
    if rec.get("eds", 0) >= 3:
        score += weights.get("l3_evidence", 2)
    if rec.get("abstract_words", 100) < 75:
        score -= weights.get("short_abstract_penalty", 1)

    score = max(0.0, round(score, 2))
    label = "high" if score >= 6 else "medium" if score >= 3 else "low"
    return score, label


def main():
    print("=== 15_confidence_uncertainty_depth.py ===")
    cfg     = load_config()
    scr_cfg = load_scoring_cfg()
    weights = scr_cfg.get("confidence_weights", {
        "title_match": 3, "abstract_match": 2, "keyword_match": 2,
        "section_match": 3, "multi_phrase": 2, "specific_mechanism": 2,
        "vague_term_penalty": 1, "ambiguous_penalty": 2,
        "l3_evidence": 2, "short_abstract_penalty": 1,
    })

    in_path  = Path("data/final/final_index_table.jsonl")
    out_path = Path("data/final/confidence_scored_records.jsonl")
    csv_path = Path("outputs/tables/confidence_distribution.csv")
    rpt_path = Path("outputs/reports/uncertainty_report.md")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    rpt_path.parent.mkdir(parents=True, exist_ok=True)

    records = []
    if in_path.exists():
        with open(in_path) as f:
            for line in f:
                l = line.strip()
                if l:
                    records.append(json.loads(l))

    print(f"  Input records : {len(records)}")

    scored = []
    dist = Counter()

    for rec in records:
        score, label = compute_confidence(rec, weights)
        rec["confidence_score"] = score
        rec["confidence_label"] = label
        scored.append(rec)
        dist[label] += 1

    with open(out_path, "w") as f:
        for r in scored:
            f.write(json.dumps(r) + "\n")

    total = len(scored)
    csv_rows = [{"confidence_label": k, "count": v,
                 "pct": f"{v/total*100:.1f}%"} for k, v in dist.items()]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["confidence_label","count","pct"])
        writer.writeheader()
        writer.writerows(csv_rows)

    # Uncertainty report
    rpt = f"""# Uncertainty Report

Total records scored: {total}
High confidence   : {dist['high']} ({dist['high']/total*100:.1f}%)
Medium confidence : {dist['medium']} ({dist['medium']/total*100:.1f}%)
Low confidence    : {dist['low']} ({dist['low']/total*100:.1f}%)

## Confidence Weights Used
{yaml.dump(weights, default_flow_style=False)}

## Sensitivity Analysis Note
Main results are reported for all records.
Sensitivity analyses repeat key analyses on high-confidence records only.
See 17_statistical_analysis.py for sensitivity runs.

## Limitation
Confidence scoring is heuristic. Low-confidence records may still be
correctly classified; conversely, high-confidence records may contain
surface-level term matches without deep semantic correspondence.
"""
    rpt_path.write_text(rpt)

    print(f"  High   : {dist['high']}")
    print(f"  Medium : {dist['medium']}")
    print(f"  Low    : {dist['low']}")
    print(f"  Output : {out_path}")
    print("  Done.")


if __name__ == "__main__":
    main()
