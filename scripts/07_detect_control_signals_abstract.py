#!/usr/bin/env python3
"""
Script 07 — Detect Control Signals (CSDS and CSS Scoring)
===========================================================
Scores each paper on:
  CSDS (Control Signal Depth Score, 0-5): highest matching control level
  CSS  (Control Specificity Score, 0-3):  specificity of control language

Derives:
  gap_a: high_agency AND CSDS == 0
  gap_b: high_agency AND CSS <= gap_b_css_threshold (default: 1)
  under_specified: high_agency AND CSS <= under_spec_threshold AND no L3 evidence

Input:  data/normalized/agency_scored_records.jsonl
Output: data/normalized/control_scored_records.jsonl
"""
import argparse, json, os, re
import yaml

def score_csds(text, level_terms):
    text_lower = text.lower()
    max_level = 0
    for level_str, level_data in level_terms.items():
        level = int(level_str)
        if level == 0:
            continue
        terms = level_data.get("trigger_terms", [])
        for term in terms:
            if str(term).lower() in text_lower:
                max_level = max(max_level, level)
                break
    return max_level

def score_css(text, css_levels):
    text_lower = text.lower()
    # Level 3: named specific mechanism (heuristic: quoted UI element or named button)
    if re.search(r"'[^']{3,30}'|\"[^\"]{3,30}\"|button|slider|checkbox|toggle|widget", text_lower):
        # Check context: near a control term
        if any(t in text_lower for t in ["override", "undo", "reject", "approve", "rollback"]):
            return 3
    # Level 2: generic control action named
    generic = ["edit outputs", "reject ", "regenerate", "select from", "choose from",
                "edit the", "modify the", "override the", "approve the"]
    if any(g in text_lower for g in generic):
        return 2
    # Level 1: vague control claim
    vague = ["users can control", "user has control", "gives users control",
             "allows control", "user is in control", "human control", "user control"]
    if any(v in text_lower for v in vague):
        return 1
    return 0

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/config.yaml")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)
    with open("config/control_terms.yaml") as f:
        ctrl_cfg = yaml.safe_load(f)

    level_terms = ctrl_cfg["csds_levels"]
    gap_a_thresh = cfg["scoring"]["gap_a_csds_threshold"]
    gap_b_thresh = cfg["scoring"]["gap_b_css_threshold"]
    under_spec_thresh = cfg["scoring"]["under_spec_css_threshold"]

    in_path = os.path.join(cfg["paths"]["normalized"], "agency_scored_records.jsonl")
    out_dir = cfg["paths"]["normalized"]

    records = []
    with open(in_path, encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line.strip()))

    for rec in records:
        text = f"{rec.get('title','')} {rec.get('abstract_filtered', rec.get('abstract',''))}"
        csds = score_csds(text, level_terms)
        css = score_css(text, ctrl_cfg.get("css_levels", {}))
        rec["csds"] = csds
        rec["css"] = css
        ha = rec.get("high_agency", False)
        rec["gap_a"] = ha and (csds <= gap_a_thresh)
        rec["gap_b"] = ha and (css <= gap_b_thresh)
        # under_specified requires no L3 evidence clarifying control; at L1/L2, treat as under-specified if CSS <= threshold
        rec["under_specified"] = ha and (css <= under_spec_thresh) and not rec.get("l3_evidence", False)

    out_path = os.path.join(out_dir, "control_scored_records.jsonl")
    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    gap_a_n = sum(1 for r in records if r["gap_a"])
    under_n = sum(1 for r in records if r["under_specified"])
    print(f"Control scoring complete: {len(records)} records")
    print(f"  Gap A (high-agency + CSDS=0): {gap_a_n}")
    print(f"  Under-specified: {under_n}")

if __name__ == "__main__":
    main()
