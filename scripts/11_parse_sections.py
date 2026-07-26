"""
11_parse_sections.py
=====================
Parse full-text files into labelled sections using heuristic
heading detection.  Produces a structured JSON per paper and
records section-parsing quality metrics.

Section priority order for control evidence:
  1. system / design / interface
  2. method
  3. evaluation
  4. abstract
  5. discussion

Section priority order for evaluation evidence:
  1. evaluation
  2. method
  3. results
  4. abstract

Inputs
------
data/fulltext/<doi_safe>.txt
data/final/deep_enrichment_subset.jsonl

Outputs
-------
data/sections/<doi_safe>_sections.json
outputs/reports/section_parsing_check_report.md
outputs/tables/section_parsing_quality.csv
"""

import json, re, yaml, csv
from pathlib import Path


SECTION_PATTERNS = {
    "abstract":    r"\b(abstract)\b",
    "introduction":r"\b(introduction|background)\b",
    "related":     r"\b(related work|literature review)\b",
    "system":      r"\b(system|interface|design|prototype|tool)\b",
    "method":      r"\b(method|methodology|approach|procedure)\b",
    "evaluation":  r"\b(evaluation|user study|experiment|study design)\b",
    "results":     r"\b(results|findings|outcomes)\b",
    "discussion":  r"\b(discussion|implications)\b",
    "limitations": r"\b(limitations|threats to validity)\b",
    "conclusion":  r"\b(conclusion|summary|future work)\b",
}

# Evidence section priority lists from plan
CONTROL_SECTION_PRIORITY  = ["system","method","evaluation","abstract","discussion"]
EVAL_SECTION_PRIORITY     = ["evaluation","method","results","abstract"]


def load_config(path: str = "config/config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def split_into_sections(text: str) -> dict[str, str]:
    """Heuristic section splitting based on heading patterns."""
    lines = text.split("\n")
    sections: dict[str, list[str]] = {"full_text": []}
    current_section = "full_text"

    for line in lines:
        stripped = line.strip()
        if len(stripped) < 80 and len(stripped) > 2:
            for sec_name, pattern in SECTION_PATTERNS.items():
                if re.search(pattern, stripped, re.IGNORECASE):
                    current_section = sec_name
                    sections.setdefault(current_section, [])
                    break
        sections.setdefault(current_section, []).append(line)

    return {k: "\n".join(v).strip() for k, v in sections.items() if v}


def quality_check(sections: dict, doi: str) -> dict:
    """Check extraction quality per plan §14."""
    checks = {
        "has_abstract":        "abstract" in sections and len(sections["abstract"]) > 50,
        "has_heading_detect":  len(sections) > 2,
        "has_method_or_eval":  "method" in sections or "evaluation" in sections,
        "has_system_section":  "system" in sections,
        "text_readable":       len(sections.get("full_text", "")) > 500,
        "section_count":       len(sections),
    }
    checks["overall_ok"] = (
        checks["has_abstract"] and
        checks["has_heading_detect"] and
        checks["text_readable"]
    )
    return checks


def main():
    print("=== 11_parse_sections.py ===")
    cfg = load_config()

    ft_dir   = Path("data/fulltext")
    sec_dir  = Path("data/sections")
    rpt_md   = Path("outputs/reports/section_parsing_check_report.md")
    rpt_csv  = Path("outputs/tables/section_parsing_quality.csv")
    sec_dir.mkdir(parents=True, exist_ok=True)
    rpt_md.parent.mkdir(parents=True, exist_ok=True)

    subset_path = Path("data/final/deep_enrichment_subset.jsonl")
    subset = []
    if subset_path.exists():
        with open(subset_path) as f:
            for line in f:
                l = line.strip()
                if l:
                    subset.append(json.loads(l))

    doi_map = {r.get("doi", ""): r for r in subset}
    ft_files = list(ft_dir.glob("*.txt"))
    print(f"  Full-text files : {len(ft_files)}")

    quality_rows = []
    ok_count = 0

    for ft_file in ft_files:
        text = ft_file.read_text(errors="replace")
        if "[PDF_RETRIEVED_NO_PARSER]" in text:
            continue

        sections = split_into_sections(text)
        doi_safe = ft_file.stem
        doi = doi_safe.replace("_", "/")  # approximate reverse

        # Add evidence section priorities
        sections["_control_priority_text"] = " ".join(
            sections.get(s, "") for s in CONTROL_SECTION_PRIORITY if s in sections
        )
        sections["_eval_priority_text"] = " ".join(
            sections.get(s, "") for s in EVAL_SECTION_PRIORITY if s in sections
        )

        out_path = sec_dir / f"{doi_safe}_sections.json"
        with open(out_path, "w") as f:
            json.dump({"doi_safe": doi_safe, "sections": sections}, f, indent=2)

        qc = quality_check(sections, doi_safe)
        if qc["overall_ok"]:
            ok_count += 1

        quality_rows.append({
            "doi_safe":            doi_safe,
            "section_count":       qc["section_count"],
            "has_abstract":        qc["has_abstract"],
            "has_method_or_eval":  qc["has_method_or_eval"],
            "has_system_section":  qc["has_system_section"],
            "text_readable":       qc["text_readable"],
            "overall_ok":          qc["overall_ok"],
        })

    total = len(quality_rows)
    pct_ok = ok_count / total * 100 if total > 0 else 0
    print(f"  Parsed         : {total}")
    print(f"  Overall OK     : {ok_count}/{total} ({pct_ok:.1f}%)")
    status = "SUFFICIENT" if pct_ok >= 80 else "EXPLORATORY ONLY"
    print(f"  Status         : {status} (target ≥80%)")

    if quality_rows:
        with open(rpt_csv, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(quality_rows[0].keys()))
            writer.writeheader()
            writer.writerows(quality_rows)

    # Markdown report
    rpt_text = f"""# Section Parsing Quality Report

Total files parsed: {total}  
Acceptable extraction (overall_ok): {ok_count}/{total} ({pct_ok:.1f}%)  
Target: ≥80% acceptable  
Status: **{status}**

{'L3 results are treated as exploratory only due to low parsing success rate.' if pct_ok < 80 else 'L3 results are used to supplement abstract-level findings.'}

## Quality Criteria
- has_abstract: abstract section detected and >50 chars
- has_heading_detect: >2 distinct sections detected
- has_method_or_eval: method or evaluation section detected
- text_readable: full text >500 chars

## Notes
Section detection is heuristic. Short/non-standard papers may fail.
Detailed results: outputs/tables/section_parsing_quality.csv
"""
    rpt_md.parent.mkdir(parents=True, exist_ok=True)
    rpt_md.write_text(rpt_text)
    print(f"  Report : {rpt_md}")
    print("  Done.")


if __name__ == "__main__":
    main()
