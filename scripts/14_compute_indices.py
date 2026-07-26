"""
14_compute_indices.py
======================
Merge abstract-level (L1) and section-level (L3) scores into a
final unified index table per record.

Computes:
  - Final TAFS, CSDS, CSS (best available: L3 > L1)
  - Final ESRS-8 (best available)
  - Evidence Depth Score (EDS 0–3)
  - Gap flags (A, B, C, D)
  - Capability under-specification flag
  - AI-type flags

Inputs
------
data/classified/*   or data/filtered/classified_records.jsonl
data/sections/section_control_signals.jsonl
data/sections/section_eval_signals.jsonl

Outputs
-------
data/final/final_index_table.jsonl
outputs/open_data/ai_hci_evidence_map_open_data.csv
"""

import json, yaml, csv
from pathlib import Path


def load_config(path: str = "config/config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def load_jsonl(path: Path) -> list[dict]:
    records = []
    if path.exists():
        with open(path) as f:
            for line in f:
                l = line.strip()
                if l:
                    records.append(json.loads(l))
    return records


def compute_eds(rec: dict, has_sections: bool) -> int:
    """Evidence Depth Score 0–3."""
    if has_sections:
        return 3
    if rec.get("abstract_word_count", 0) >= 75:
        return 2
    if rec.get("has_abstract", False):
        return 1
    return 0


def main():
    print("=== 14_compute_indices.py ===")
    cfg = load_config()
    thresholds = cfg.get("thresholds", {})
    high_agency_min_tafs = thresholds.get("high_agency_min_tafs", 3)

    # Load sources
    abstract_records = (
        load_jsonl(Path("data/final/core_corpus_scored.jsonl")) or
        load_jsonl(Path("data/filtered/classified_records.jsonl"))
    )
    section_ctrl  = {r["doi_safe"]: r for r in
                     load_jsonl(Path("data/sections/section_control_signals.jsonl"))}
    section_eval  = {r["doi_safe"]: r for r in
                     load_jsonl(Path("data/sections/section_eval_signals.jsonl"))}

    print(f"  Abstract records  : {len(abstract_records)}")
    print(f"  Section-ctrl recs : {len(section_ctrl)}")
    print(f"  Section-eval recs : {len(section_eval)}")

    out_path  = Path("data/final/final_index_table.jsonl")
    csv_path  = Path("outputs/open_data/ai_hci_evidence_map_open_data.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    final_records = []
    gap_a_count = gap_b_count = gap_c_count = gap_d_count = 0

    for rec in abstract_records:
        doi     = rec.get("doi", "")
        doi_safe = doi.replace("/","_").replace(":","_")[:120]

        # Resolve best available scores
        s_ctrl  = section_ctrl.get(doi_safe, {})
        s_eval  = section_eval.get(doi_safe, {})
        has_l3  = bool(s_ctrl)

        tafs_l1 = rec.get("tafs_score", 0)
        csds_l1 = rec.get("csds_score", 0)
        css_l1  = rec.get("css_score", 0)
        esrs_l1 = rec.get("esrs_score", 0)

        csds_final = s_ctrl.get("csds_l3", csds_l1) if has_l3 else csds_l1
        css_final  = s_ctrl.get("css_l3", css_l1) if has_l3 else css_l1
        esrs_final = s_eval.get("esrs_l3", esrs_l1) if has_l3 else esrs_l1

        high_agency   = tafs_l1 >= high_agency_min_tafs

        # Gap flags
        gap_a = high_agency and csds_l1 == 0
        gap_b = high_agency and css_l1 <= 1
        gap_c = gap_a and csds_final > 0   # resolved by L3
        gap_d = gap_a and csds_final == 0  # persistent

        under_specified = high_agency and css_l1 <= 1 and not has_l3

        eds = compute_eds(rec, has_l3)

        if gap_a: gap_a_count += 1
        if gap_b: gap_b_count += 1
        if gap_c: gap_c_count += 1
        if gap_d: gap_d_count += 1

        final = {
            "doi":             doi,
            "title":           rec.get("title", ""),
            "year":            rec.get("year", ""),
            "venue":           rec.get("venue", ""),
            "abstract_words":  rec.get("abstract_word_count", 0),
            "tafs":            tafs_l1,
            "csds_l1":         csds_l1,
            "csds_final":      csds_final,
            "css_l1":          css_l1,
            "css_final":       css_final,
            "esrs_l1":         esrs_l1,
            "esrs_final":      esrs_final,
            "eds":             eds,
            "high_agency":     high_agency,
            "gap_a":           gap_a,
            "gap_b":           gap_b,
            "gap_c_resolved":  gap_c,
            "gap_d_persistent":gap_d,
            "under_specified": under_specified,
            "genai_flag":      rec.get("genai_flag", False),
            "llm_flag":        rec.get("llm_flag", False),
            "agentic_flag":    rec.get("agentic_flag", False),
            "ai_type":         rec.get("ai_type", ""),
        }
        final_records.append(final)

    with open(out_path, "w") as f:
        for r in final_records:
            f.write(json.dumps(r) + "\n")

    # CSV open data export
    if final_records:
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(final_records[0].keys()))
            writer.writeheader()
            writer.writerows(final_records)

    print(f"  Final records : {len(final_records)}")
    print(f"  Gap A (no ctrl at L1) : {gap_a_count}")
    print(f"  Gap B (vague ctrl)    : {gap_b_count}")
    print(f"  Gap C (resolved by L3): {gap_c_count}")
    print(f"  Gap D (persistent)    : {gap_d_count}")
    print(f"  Output : {out_path}")
    print(f"  CSV    : {csv_path}")
    print("  Done.")


if __name__ == "__main__":
    main()
