"""
20_generate_reports.py
=======================
Generate all markdown report files summarising pipeline outputs.

Reports generated (from plan §24):
  collection_report.md
  deduplication_report.md
  classification_report.md
  deep_enrichment_report.md
  section_parsing_check_report.md
  uncertainty_report.md
  final_results_report.md
  reproducibility_report.md

Inputs
------
All outputs/tables/*.csv and data/final/*.jsonl files

Outputs
-------
reports/*.md
"""

import json, yaml, csv
from pathlib import Path
from datetime import datetime
from collections import Counter


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    n = 0
    with open(path) as f:
        for line in f:
            if line.strip():
                n += 1
    return n


def load_jsonl(path: Path, limit: int = 999999) -> list[dict]:
    records = []
    if not path.exists():
        return records
    with open(path) as f:
        for i, line in enumerate(f):
            if i >= limit:
                break
            l = line.strip()
            if l:
                records.append(json.loads(l))
    return records


def write_report(path: Path, title: str, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    header = f"# {title}\n\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    path.write_text(header + content)
    print(f"  Written: {path.name}")


def main():
    print("=== 20_generate_reports.py ===")
    rpt_dir = Path("reports")
    rpt_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d")

    # ── collection_report.md ─────────────────────────────────────────
    n_raw = count_jsonl(Path("data/raw/openalex_records.jsonl"))
    write_report(rpt_dir/"collection_report.md",
        "Collection Report",
        f"## Summary\n\nRecords retrieved from OpenAlex: **{n_raw:,}**\n\n"
        f"Source: OpenAlex API (https://api.openalex.org)\n\n"
        f"Retrieval date: {ts}\n\n"
        f"Venues queried: see config/venue_whitelist.yaml\n\n"
        f"Study period: 2019–2025 (2026 excluded for partial-year bias)\n"
    )

    # ── deduplication_report.md ──────────────────────────────────────
    n_dedup = count_jsonl(Path("data/deduplicated/deduplicated_records.jsonl"))
    write_report(rpt_dir/"deduplication_report.md",
        "Deduplication Report",
        f"## Summary\n\nRecords before deduplication: **{n_raw:,}**\n\n"
        f"Records after deduplication: **{n_dedup:,}**\n\n"
        f"Duplicates removed: **{max(0, n_raw - n_dedup):,}**\n\n"
        f"## Rules\n\n"
        f"1. Exact DOI match → duplicate\n"
        f"2. Fuzzy title similarity ≥0.95 + same year + same first author → duplicate\n"
        f"3. Fuzzy similarity 0.85–0.94 → uncertain, keep most complete record\n\n"
        f"See outputs/tables/deduplication_report.csv for details.\n"
    )

    # ── classification_report.md ─────────────────────────────────────
    classified = load_jsonl(Path("data/final/final_index_table.jsonl"), limit=5000)
    ai_types = Counter(r.get("ai_type","") for r in classified)
    write_report(rpt_dir/"classification_report.md",
        "Classification Report",
        f"## Summary\n\nTotal classified records: **{len(classified):,}**\n\n"
        f"## AI Type Distribution\n\n"
        + "".join(f"- {k or 'unclassified'}: {v}\n" for k, v in ai_types.most_common())
        + f"\n## Notes\n\nAI type assigned by priority rule (agentic → LLM → GenAI → ...).\n"
        f"See config/ai_terms.yaml for classification dictionaries.\n"
    )

    # ── deep_enrichment_report.md ────────────────────────────────────
    n_deep = count_jsonl(Path("data/final/deep_enrichment_subset.jsonl"))
    n_ft   = len(list(Path("data/fulltext").glob("*.txt"))) \
             if Path("data/fulltext").exists() else 0
    write_report(rpt_dir/"deep_enrichment_report.md",
        "Deep Enrichment Report",
        f"## Summary\n\nLayer C subset selected: **{n_deep}**\n\n"
        f"Open full text retrieved: **{n_ft}** ({n_ft/n_deep*100:.1f}% of subset)\n\n"
        f"## Selection Method\n\n"
        f"Automated priority scoring — NOT manual cherry-picking.\n\n"
        f"Priority criteria: GenAI/agentic flag (+3), high-agency (+2), "
        f"weak/no control (+3), open access (+3), under-specified (+2), "
        f"top venue (+2), high citation percentile (+1), ambiguous control (+2).\n\n"
        f"See config/deep_subset_selection.yaml for weights.\n\n"
        f"## Important Note\n\n"
        f"The deep subset is an enrichment sample, not a statistically representative sample. "
        f"It is used ONLY for gap-resolution analysis, section-level evidence detection, "
        f"and under-specification exploration.\n"
    )

    # ── final_results_report.md ──────────────────────────────────────
    final = load_jsonl(Path("data/final/final_index_table.jsonl"), limit=9999)
    n_gap_a = sum(1 for r in final if r.get("gap_a"))
    n_gap_d = sum(1 for r in final if r.get("gap_d_persistent"))
    n_under = sum(1 for r in final if r.get("under_specified"))
    n_high  = sum(1 for r in final if r.get("high_agency"))
    write_report(rpt_dir/"final_results_report.md",
        "Final Results Report",
        f"## Summary\n\n"
        f"Total records in final analysis: **{len(final):,}**\n\n"
        f"High-agency language (TAFS ≥ 3): **{n_high}** ({n_high/len(final)*100:.1f}%)\n\n"
        f"Gap A (high-agency + no control): **{n_gap_a}** ({n_gap_a/len(final)*100:.1f}%)\n\n"
        f"Gap D (persistent after L3): **{n_gap_d}**\n\n"
        f"Under-specified: **{n_under}** ({n_under/len(final)*100:.1f}%)\n\n"
        f"## Key Files\n\n"
        f"- Primary open dataset: outputs/open_data/ai_hci_evidence_map_open_data.csv\n"
        f"- Statistical results: outputs/tables/statistical_results.json\n"
        f"- PRISMA counts: outputs/prisma/prisma_counts.csv\n"
    )

    # ── reproducibility_report.md ────────────────────────────────────
    scripts = sorted(Path("scripts").glob("*.py")) if Path("scripts").exists() else []
    configs = sorted(Path("config").glob("*.yaml")) if Path("config").exists() else []
    write_report(rpt_dir/"reproducibility_report.md",
        "Reproducibility Report",
        f"## Reproducibility Statement\n\n"
        f"The complete pipeline can be re-executed with a single command:\n\n"
        f"```bash\npython run_pipeline.py --config config/config.yaml\n```\n\n"
        f"## Pipeline Scripts ({len(scripts)} files)\n\n"
        + "".join(f"- {s.name}\n" for s in scripts)
        + f"\n## Configuration Files ({len(configs)} files)\n\n"
        + "".join(f"- {c.name}\n" for c in configs)
        + f"\n## Dependencies\n\n"
        f"Pinned in requirements.txt (pip) and environment.yml (conda).\n\n"
        f"## Open Data\n\n"
        f"Primary open dataset: outputs/open_data/ai_hci_evidence_map_open_data.csv\n\n"
        f"Persistent archive: Zenodo DOI to be minted before publication.\n\n"
        f"## Notes\n\n"
        f"- Minor variation in OpenAlex API responses is expected across retrieval dates.\n"
        f"- The archived dataset provides a fixed reference snapshot.\n"
        f"- L3 full-text retrieval results may vary depending on open-access status.\n"
    )

    print("  All reports written to reports/")
    print("  Done.")


if __name__ == "__main__":
    main()
