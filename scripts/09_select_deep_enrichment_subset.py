"""
09_select_deep_enrichment_subset.py
====================================
Automatically select the deep-enrichment subset (Layer C) of
100–150 papers using a priority scoring scheme.  Selection is
entirely rule-based — no manual cherry-picking.

Inputs
------
data/filtered/classified_records.jsonl
config/deep_subset_selection.yaml

Outputs
-------
data/final/deep_enrichment_subset.jsonl
outputs/tables/deep_enrichment_selection_report.csv
"""

import json, yaml, csv
from pathlib import Path
from dataclasses import dataclass, field, asdict


def load_config(path: str = "config/config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def load_deep_cfg(path: str = "config/deep_subset_selection.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


@dataclass
class ScoredRecord:
    doi: str
    title: str
    year: int
    genai_flag: bool
    llm_flag: bool
    agentic_flag: bool
    high_agency: bool
    csds: int
    css: int
    has_abstract: bool
    abstract_word_count: int
    top_venue: bool
    open_access: bool
    under_specified: bool
    priority_score: float = 0.0


def compute_priority(rec: dict, weights: dict) -> float:
    """
    Priority scoring from the plan:
    +3 GenAI/LLM/agentic flag
    +2 high-agency language
    +3 weak/no control signal
    +2 ambiguous control context
    +2 top HCI venue
    +1 high citation percentile
    +3 open-access full text available
    +2 under-specified capability
    """
    score = 0.0

    if rec.get("genai_flag") or rec.get("llm_flag") or rec.get("agentic_flag"):
        score += weights.get("genai_agentic", 3)

    if rec.get("high_agency", False):
        score += weights.get("high_agency", 2)

    csds = rec.get("csds_score", 5)
    if csds == 0:
        score += weights.get("no_control", 3)
    elif csds <= 1:
        score += weights.get("weak_control", 2)

    if rec.get("control_ambiguous", False):
        score += weights.get("ambiguous_control", 2)

    if rec.get("top_venue", False):
        score += weights.get("top_venue", 2)

    if rec.get("citation_percentile", 0) >= 75:
        score += weights.get("high_citation", 1)

    if rec.get("open_access", False):
        score += weights.get("open_access", 3)

    if rec.get("under_specified", False):
        score += weights.get("under_specified", 2)

    if rec.get("abstract_word_count", 100) < 75:
        score -= weights.get("short_abstract_penalty", 1)

    return round(score, 2)


def main():
    print("=== 09_select_deep_enrichment_subset.py ===")
    cfg = load_config()
    deep_cfg = load_deep_cfg()

    weights     = deep_cfg.get("priority_weights", {})
    target_n    = deep_cfg.get("target_size", 150)
    min_score   = deep_cfg.get("min_priority_score", 4)
    oa_required = deep_cfg.get("require_open_access", False)

    in_path  = Path("data/filtered/classified_records.jsonl")
    out_path = Path("data/final/deep_enrichment_subset.jsonl")
    rpt_path = Path("outputs/tables/deep_enrichment_selection_report.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rpt_path.parent.mkdir(parents=True, exist_ok=True)

    records = []
    if in_path.exists():
        with open(in_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))

    print(f"  Input records : {len(records)}")

    for rec in records:
        rec["_priority_score"] = compute_priority(rec, weights)

    # Filter by minimum score and optional OA requirement
    candidates = [r for r in records if r["_priority_score"] >= min_score]
    if oa_required:
        candidates = [r for r in candidates if r.get("open_access", False)]

    # Sort descending by priority score; take top N
    candidates.sort(key=lambda r: r["_priority_score"], reverse=True)
    selected = candidates[:target_n]

    print(f"  Candidates (score ≥ {min_score}) : {len(candidates)}")
    print(f"  Selected (top {target_n})          : {len(selected)}")

    with open(out_path, "w") as f:
        for rec in selected:
            f.write(json.dumps(rec) + "\n")

    # Report
    report_rows = []
    for rec in selected:
        report_rows.append({
            "doi":            rec.get("doi", ""),
            "year":           rec.get("year", ""),
            "priority_score": rec["_priority_score"],
            "open_access":    rec.get("open_access", False),
            "high_agency":    rec.get("high_agency", False),
            "csds_score":     rec.get("csds_score", ""),
            "genai_flag":     rec.get("genai_flag", False),
            "agentic_flag":   rec.get("agentic_flag", False),
            "under_specified":rec.get("under_specified", False),
        })

    if report_rows:
        with open(rpt_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(report_rows[0].keys()))
            writer.writeheader()
            writer.writerows(report_rows)

    print(f"  Output : {out_path}")
    print(f"  Report : {rpt_path}")
    print("  Done — Layer C selection complete.")
    print("  NOTE: Deep subset is an enrichment sample, not a statistically")
    print("        representative sample. Use for gap-resolution only.")


if __name__ == "__main__":
    main()
