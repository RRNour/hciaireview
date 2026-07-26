"""
13_detect_evaluation_signals_sections.py
==========================================
Apply ESRS-8 evaluation-signal detection to section-level text
from the deep-enrichment subset.

Produces ESRS score at L3 (section level) for comparison with
abstract-level (L1) ESRS.

Inputs
------
data/sections/*_sections.json
config/evaluation_terms.yaml

Outputs
-------
data/sections/section_eval_signals.jsonl
outputs/tables/esrs_l1_vs_l3.csv
"""

import json, yaml, re, csv
from pathlib import Path


def load_eval_cfg(path: str = "config/evaluation_terms.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def score_esrs(text: str, cfg: dict) -> dict:
    """Score 8 ESRS dimensions; return dict of {dim: bool} and total."""
    dims = cfg.get("esrs_dimensions", {})
    scores = {}
    total = 0
    for dim_name, dim_cfg in dims.items():
        terms = dim_cfg.get("terms", [])
        matched = any(re.search(re.escape(t), text, re.IGNORECASE) for t in terms)
        scores[f"esrs_{dim_name}"] = matched
        if matched:
            total += 1
    scores["esrs_l3_total"] = total
    return scores


def main():
    print("=== 13_detect_evaluation_signals_sections.py ===")
    eval_cfg = load_eval_cfg()

    sec_dir  = Path("data/sections")
    out_path = Path("data/sections/section_eval_signals.jsonl")
    rpt_path = Path("outputs/tables/esrs_l1_vs_l3.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rpt_path.parent.mkdir(parents=True, exist_ok=True)

    # Load subset for L1 ESRS comparison
    subset_by_doi = {}
    subset_path = Path("data/final/deep_enrichment_subset.jsonl")
    if subset_path.exists():
        with open(subset_path) as f:
            for line in f:
                l = line.strip()
                if l:
                    rec = json.loads(l)
                    subset_by_doi[rec.get("doi", "")] = rec

    section_files = list(sec_dir.glob("*_sections.json"))
    print(f"  Section files : {len(section_files)}")

    results = []
    rpt_rows = []

    for sf in section_files:
        data     = json.loads(sf.read_text())
        doi_safe = data.get("doi_safe", sf.stem)
        sections = data.get("sections", {})

        # Priority text for evaluation detection
        priority_text = " ".join(
            sections.get(s, "")
            for s in ["evaluation","method","results","abstract"]
        )

        dim_scores = score_esrs(priority_text, eval_cfg)
        esrs_l3    = dim_scores.pop("esrs_l3_total", 0)

        doi_approx = doi_safe.replace("_", "/")
        l1_rec     = subset_by_doi.get(doi_approx, {})
        esrs_l1    = l1_rec.get("esrs_score", 0)

        result = {
            "doi_safe": doi_safe,
            "esrs_l3":  esrs_l3,
            "esrs_l1":  esrs_l1,
            "esrs_delta": esrs_l3 - esrs_l1,
            **dim_scores,
        }
        results.append(result)
        rpt_rows.append({
            "doi_safe":    doi_safe,
            "esrs_l1":     esrs_l1,
            "esrs_l3":     esrs_l3,
            "esrs_delta":  esrs_l3 - esrs_l1,
        })

    with open(out_path, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    if rpt_rows:
        with open(rpt_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rpt_rows[0].keys()))
            writer.writeheader()
            writer.writerows(rpt_rows)

    mean_delta = sum(r["esrs_delta"] for r in rpt_rows)/len(rpt_rows) if rpt_rows else 0
    print(f"  Processed      : {len(results)}")
    print(f"  Mean ESRS L3-L1 delta : {mean_delta:+.2f}")
    print(f"  Output : {out_path}")
    print("  Done.")


if __name__ == "__main__":
    main()
