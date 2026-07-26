"""
19_generate_prisma_counts.py
=============================
Aggregate PRISMA-like flow counts from pipeline log files and
write a structured CSV + PNG flow diagram.

Stages tracked (from plan §23):
  1. records_retrieved
  2. records_after_dedup
  3. records_ai_terms
  4. records_hci_terms
  5. records_broad_corpus
  6. records_core_hci
  7. records_with_abstracts
  8. records_deep_enrichment
  9. records_open_fulltext
  10. records_parsed_sections
  11. records_final_analysis

Inputs
------
outputs/tables/deduplication_report.csv  (script 03)
outputs/tables/filter_counts.json        (scripts 04/01)
data/final/deep_enrichment_subset.jsonl
data/fulltext/    (count files)
data/sections/    (count files)
data/final/final_index_table.jsonl

Outputs
-------
outputs/prisma/prisma_counts.csv
outputs/prisma/prisma_flow.png
"""

import json, csv, os
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

NAVY  = "#1F4E79"
BLUE  = "#2E75B6"
LBLUE = "#D6E4F0"
GREEN = "#1E8449"
LGREEN= "#D5F5E3"
AMBER = "#D68910"
LAMBER= "#FEF9E7"
GRAY  = "#595959"
LGRAY = "#F2F2F2"
WHITE = "#FFFFFF"


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    n = 0
    with open(path) as f:
        for line in f:
            if line.strip():
                n += 1
    return n


def load_filter_counts(path: Path) -> dict:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def main():
    print("=== 19_generate_prisma_counts.py ===")

    out_dir = Path("outputs/prisma")
    out_dir.mkdir(parents=True, exist_ok=True)

    fc = load_filter_counts(Path("outputs/tables/filter_counts.json"))

    counts = {
        "records_retrieved":       fc.get("records_retrieved", 0),
        "records_after_dedup":     fc.get("records_after_dedup", 0),
        "records_matching_ai":     fc.get("records_ai_terms", 0),
        "records_matching_hci":    fc.get("records_hci_terms", 0),
        "records_broad_corpus":    fc.get("records_broad_corpus", 0),
        "records_core_hci":        fc.get("records_core_hci",
                                      count_jsonl(Path("data/final/core_corpus_full.jsonl"))),
        "records_with_abstracts":  fc.get("records_with_abstracts",
                                      count_jsonl(Path("data/final/core_corpus_scored.jsonl"))),
        "records_deep_enrichment": count_jsonl(Path("data/final/deep_enrichment_subset.jsonl")),
        "records_open_fulltext":   len(list(Path("data/fulltext").glob("*.txt")))
                                      if Path("data/fulltext").exists() else 0,
        "records_parsed_sections": len(list(Path("data/sections").glob("*_sections.json")))
                                      if Path("data/sections").exists() else 0,
        "records_final_analysis":  count_jsonl(Path("data/final/final_index_table.jsonl")),
    }

    # Save CSV
    csv_path = out_dir / "prisma_counts.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["stage","count"])
        writer.writeheader()
        for stage, count in counts.items():
            writer.writerow({"stage": stage, "count": count})
            print(f"  {stage:<35}: {count}")

    # PRISMA flow diagram
    STAGE_GROUPS = [
        ("IDENTIFICATION", [
            ("Records identified", counts["records_retrieved"]),
            ("After deduplication", counts["records_after_dedup"]),
        ], LBLUE, NAVY),
        ("SCREENING", [
            ("Matching AI terms", counts["records_matching_ai"]),
            ("Matching HCI terms", counts["records_matching_hci"]),
            ("Broad corpus (Layer A)", counts["records_broad_corpus"]),
        ], LAMBER, AMBER),
        ("ELIGIBILITY", [
            ("Core HCI corpus (Layer B)", counts["records_core_hci"]),
            ("With ≥75-word abstracts", counts["records_with_abstracts"]),
        ], "#FDEBD0", "#CA6F1E"),
        ("INCLUDED", [
            ("Deep enrichment subset (Layer C)", counts["records_deep_enrichment"]),
            ("Open full text retrieved", counts["records_open_fulltext"]),
            ("Parsed sections", counts["records_parsed_sections"]),
            ("Final analysis", counts["records_final_analysis"]),
        ], LGREEN, GREEN),
    ]

    fig, ax = plt.subplots(figsize=(10, 14))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, len(sum([g[1] for g in STAGE_GROUPS], [])) * 2.5 + 2)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    y = ax.get_ylim()[1] - 1.5
    for group_name, stages, fill, ec in STAGE_GROUPS:
        ax.text(0.2, y + 0.6, group_name, fontsize=9, fontweight="bold",
                color=ec, rotation=90, va="center")
        for stage_name, count in stages:
            rect = mpatches.FancyBboxPatch(
                (0.8, y - 0.6), 7.0, 1.2,
                boxstyle="round,pad=0.1", facecolor=fill,
                edgecolor=ec, linewidth=1.5, zorder=2
            )
            ax.add_patch(rect)
            ax.text(4.3, y, f"{stage_name}\nn = {count:,}",
                    ha="center", va="center", fontsize=10,
                    color="#1A1A1A", fontweight="medium", zorder=3)
            if y - 1.5 > 0:
                ax.annotate("", xy=(4.3, y - 0.7), xytext=(4.3, y - 1.2),
                            arrowprops=dict(arrowstyle="-|>",
                                           color="#777777", lw=1.5))
            y -= 2.5

    ax.set_title("PRISMA-Style Flow Diagram — AI-HCI Evidence Map Pipeline",
                 fontsize=12, fontweight="bold", color=NAVY, pad=16)

    fig_path = out_dir / "prisma_flow.png"
    fig.savefig(fig_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    print(f"\n  CSV  : {csv_path}")
    print(f"  PNG  : {fig_path}")
    print("  Done.")


if __name__ == "__main__":
    main()
