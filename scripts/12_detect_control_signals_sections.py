"""
12_detect_control_signals_sections.py
======================================
Apply control-signal detection (CSDS, CSS) to section-level text
from the deep-enrichment subset (L3 evidence).

Computes:
  - csds_l3:  Control Signal Depth Score from section text
  - css_l3:   Control Specificity Score from section text
  - gap_l1_resolved: Gap A at L1 resolved by L3 evidence
  - gap_persistent:  Gap A persists at L3 (Gap D)

Inputs
------
data/sections/*_sections.json
data/final/deep_enrichment_subset.jsonl
config/control_terms.yaml

Outputs
-------
data/sections/section_control_signals.jsonl
outputs/tables/gap_resolution_l1_vs_l3.csv
"""

import json, yaml, re, csv
from pathlib import Path


def load_config(path: str = "config/config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def load_control_cfg(path: str = "config/control_terms.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def apply_polysemy_filter(text: str, window: int = 5) -> str:
    """Remove 'control' tokens near experimental-design words."""
    cfg = load_control_cfg()
    exclusions = cfg.get("polysemy_exclusions", [
        "condition","group","variable","experiment","baseline",
        "trial","controlled study","control arm","control group",
        "statistical control","between-subjects","within-subjects",
    ])
    result = text
    for excl in exclusions:
        pattern = rf"\b\w+\b(?:\s+\w+){{0,{window}}}\bcontrol\b|" \
                  rf"\bcontrol\b(?:\s+\w+){{0,{window}}}\b{re.escape(excl)}\b"
        result = re.sub(pattern, " ", result, flags=re.IGNORECASE)
    return result


def score_csds(text: str, cfg: dict) -> int:
    levels = cfg.get("csds_levels", {})
    for level in sorted(levels.keys(), reverse=True):
        terms = levels[level].get("terms", [])
        for term in terms:
            if re.search(re.escape(term), text, re.IGNORECASE):
                return int(level)
    return 0


def score_css(text: str, cfg: dict) -> int:
    css_cfg = cfg.get("css_levels", {})
    for level in sorted(css_cfg.keys(), reverse=True):
        terms = css_cfg[level].get("terms", [])
        for term in terms:
            if re.search(re.escape(term), text, re.IGNORECASE):
                return int(level)
    return 0


def main():
    print("=== 12_detect_control_signals_sections.py ===")
    cfg     = load_config()
    ctl_cfg = load_control_cfg()

    sec_dir  = Path("data/sections")
    out_path = Path("data/sections/section_control_signals.jsonl")
    rpt_path = Path("outputs/tables/gap_resolution_l1_vs_l3.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rpt_path.parent.mkdir(parents=True, exist_ok=True)

    # Load deep subset to get L1 gap flags
    subset_path = Path("data/final/deep_enrichment_subset.jsonl")
    subset_by_doi = {}
    if subset_path.exists():
        with open(subset_path) as f:
            for line in f:
                l = line.strip()
                if l:
                    rec = json.loads(l)
                    doi = rec.get("doi", "")
                    if doi:
                        subset_by_doi[doi] = rec

    section_files = list(sec_dir.glob("*_sections.json"))
    print(f"  Section files : {len(section_files)}")

    results = []
    gap_report = []
    resolved = 0
    persistent = 0

    for sf in section_files:
        data = json.loads(sf.read_text())
        doi_safe = data.get("doi_safe", sf.stem)
        sections = data.get("sections", {})

        # Priority text for control detection
        priority_text = sections.get(
            "_control_priority_text",
            " ".join(sections.get(s, "") for s in
                     ["system","method","evaluation","abstract","discussion"])
        )
        filtered_text = apply_polysemy_filter(priority_text)

        csds_l3 = score_csds(filtered_text, ctl_cfg)
        css_l3  = score_css(filtered_text, ctl_cfg)

        # Approximate DOI from doi_safe
        doi_approx = doi_safe.replace("_", "/")
        l1_rec = subset_by_doi.get(doi_approx, {})
        gap_l1    = l1_rec.get("gap_a", False)
        high_agency = l1_rec.get("high_agency", False)

        # Gap resolution
        gap_l3    = high_agency and (csds_l3 == 0)
        resolved_flag = gap_l1 and not gap_l3
        persistent_flag = gap_l1 and gap_l3

        if resolved_flag: resolved += 1
        if persistent_flag: persistent += 1

        result = {
            "doi_safe":       doi_safe,
            "csds_l3":        csds_l3,
            "css_l3":         css_l3,
            "gap_l1":         gap_l1,
            "gap_l3":         gap_l3,
            "gap_l1_resolved": resolved_flag,
            "gap_persistent": persistent_flag,
        }
        results.append(result)

        gap_report.append({
            "doi_safe":   doi_safe,
            "gap_l1":     gap_l1,
            "csds_l1":    l1_rec.get("csds_score", ""),
            "csds_l3":    csds_l3,
            "css_l3":     css_l3,
            "gap_l3":     gap_l3,
            "resolved":   resolved_flag,
            "persistent": persistent_flag,
        })

    with open(out_path, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    if gap_report:
        with open(rpt_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(gap_report[0].keys()))
            writer.writeheader()
            writer.writerows(gap_report)

    n_gap_l1 = sum(1 for r in gap_report if r["gap_l1"])
    print(f"  Papers with Gap A at L1 : {n_gap_l1}")
    print(f"  Resolved by L3 evidence : {resolved}")
    print(f"  Persistent Gap (Gap D)  : {persistent}")
    print(f"  Output : {out_path}")
    print(f"  Report : {rpt_path}")
    print("  Done.")


if __name__ == "__main__":
    main()
