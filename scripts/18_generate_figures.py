"""
18_generate_figures.py
=======================
Generate all manuscript figures from the final index table.
Figures have NO embedded figure numbers in their titles —
numbering lives only in manuscript captions.

Produces all figures defined in the plan (§24):
  publication_trend.png
  genai_agentic_growth.png
  agency_framing_trend.png
  control_signal_depth_trend.png
  control_specificity_heatmap.png
  evaluation_signal_robustness.png
  agency_control_gap_by_period.png
  gap_resolution_l1_l3.png
  under_specification_by_ai_type.png
  topic_keyword_network.png  (produced by script 16)

Inputs
------
data/final/confidence_scored_records.jsonl  (or final_index_table.jsonl)

Outputs
-------
outputs/figures/*.png  (150 DPI)
"""

import json, yaml, csv
from pathlib import Path
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── Palette ───────────────────────────────────────────────────────────
NAVY  = "#1F4E79"
BLUE  = "#2E75B6"
LBLUE = "#D6E4F0"
GREEN = "#1E8449"
LGREEN= "#D5F5E3"
AMBER = "#D68910"
RED   = "#C0392B"
GRAY  = "#595959"
LGRAY = "#F2F2F2"

YEARS  = list(range(2019, 2026))
OUT    = Path("outputs/figures")
OUT.mkdir(parents=True, exist_ok=True)


def load_records() -> list[dict]:
    for path in [Path("data/final/confidence_scored_records.jsonl"),
                 Path("data/final/final_index_table.jsonl"),
                 Path("data/final/core_corpus_scored.jsonl")]:
        if path.exists():
            recs = []
            with open(path) as f:
                for line in f:
                    l = line.strip()
                    if l:
                        recs.append(json.loads(l))
            return recs
    return []


def style_ax(ax, title, xlabel="Year", ylabel=""):
    ax.set_title(title, fontsize=12, fontweight="bold", color=NAVY, pad=10)
    ax.set_xlabel(xlabel, fontsize=10, color=GRAY)
    ax.set_ylabel(ylabel, fontsize=10, color=GRAY)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#CCCCCC")
    ax.spines["bottom"].set_color("#CCCCCC")
    ax.yaxis.grid(True, color="#EEEEEE", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(colors=GRAY, labelsize=9)


def save(fig, name):
    path = OUT / f"{name}.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Saved: {name}.png")


def main():
    print("=== 18_generate_figures.py ===")
    records = load_records()
    print(f"  Records loaded : {len(records)}")

    if not records:
        print("  No records found — run scripts 01–14 first. Exiting.")
        return

    # Aggregate by year
    year_data = defaultdict(list)
    for rec in records:
        yr = rec.get("year")
        if yr and 2019 <= int(yr) <= 2025:
            year_data[int(yr)].append(rec)

    def yr_stat(yr, key, agg="count"):
        recs = year_data.get(yr, [])
        if not recs:
            return 0
        vals = [r.get(key, 0) for r in recs if r.get(key) is not None]
        if agg == "count":
            return len(recs)
        elif agg == "mean":
            return float(np.mean(vals)) if vals else 0
        elif agg == "pct_true":
            return sum(1 for v in vals if v) / len(recs) * 100 if recs else 0
        return 0

    counts = [yr_stat(yr, None, "count") for yr in YEARS]
    tafs   = [yr_stat(yr, "tafs", "mean") for yr in YEARS]
    csds   = [yr_stat(yr, "csds_final", "mean") for yr in YEARS]
    esrs   = [yr_stat(yr, "esrs_final", "mean") for yr in YEARS]
    gap_a  = [yr_stat(yr, "gap_a", "pct_true") for yr in YEARS]
    under  = [yr_stat(yr, "under_specified", "pct_true") for yr in YEARS]
    high_ag= [yr_stat(yr, "high_agency", "pct_true") for yr in YEARS]

    genai_pct  = [yr_stat(yr, "genai_flag", "pct_true") for yr in YEARS]
    agentic_pct= [yr_stat(yr, "agentic_flag", "pct_true") for yr in YEARS]
    llm_pct    = [yr_stat(yr, "llm_flag", "pct_true") for yr in YEARS]

    # ── Figure 1: Publication trend ──────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(YEARS, counts, color=BLUE, width=0.6, zorder=3)
    ax.plot(YEARS, counts, color=NAVY, linewidth=2, marker="o", markersize=6, zorder=4)
    for bar, n in zip(bars, counts):
        if n:
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1, str(n),
                    ha="center", va="bottom", fontsize=9, color=NAVY, fontweight="bold")
    ax.axvspan(2022.5, 2025.5, alpha=0.07, color=GREEN, label="GenAI period (2023–2025)")
    ax.axvline(2022.5, color=AMBER, linewidth=1.2, linestyle="--", label="GenAI transition")
    style_ax(ax, "Annual AI-HCI Paper Count in Core Corpus (2019–2025)", ylabel="Papers (n)")
    ax.set_xticks(YEARS)
    ax.set_ylim(0, max(counts or [1]) * 1.2)
    ax.legend(fontsize=9, framealpha=0.8)
    save(fig, "publication_trend")

    # ── Figure 2: GenAI / agentic growth ─────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(YEARS, genai_pct, color=BLUE, linewidth=2.2, marker="o", markersize=7,
            label="GenAI (LLM/generative/copilot)")
    ax.plot(YEARS, agentic_pct, color=RED, linewidth=2.2, marker="^", markersize=7,
            label="Agentic AI")
    ax.plot(YEARS, llm_pct, color=GREEN, linewidth=1.8, marker="s", markersize=6,
            linestyle="--", label="LLM")
    ax.axvspan(2022.5, 2025.5, alpha=0.07, color=GREEN)
    ax.axvline(2022.5, color=AMBER, linewidth=1.2, linestyle="--", label="GenAI transition")
    style_ax(ax, "GenAI and Agentic AI Papers as % of Annual Corpus (2019–2025)",
             ylabel="% of papers")
    ax.set_xticks(YEARS)
    ax.legend(fontsize=9, framealpha=0.9)
    save(fig, "genai_agentic_growth")

    # ── Figure 3: Agency framing trend ───────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.fill_between(YEARS, high_ag, alpha=0.15, color=GREEN)
    ax.plot(YEARS, high_ag, color=GREEN, linewidth=2.5, marker="o", markersize=8, zorder=4)
    for x, y in zip(YEARS, high_ag):
        if y:
            ax.text(x, y+1.5, f"{y:.0f}%", ha="center", va="bottom",
                    fontsize=9, color=GREEN, fontweight="bold")
    ax.axvspan(2022.5, 2025.5, alpha=0.07, color=GREEN)
    ax.axvline(2022.5, color=AMBER, linewidth=1.2, linestyle="--", label="GenAI transition")
    style_ax(ax, "Proportion of Papers Using High-Agency Language (TAFS ≥ 3)",
             ylabel="High-agency papers (%)")
    ax.set_xticks(YEARS)
    ax.set_ylim(0, 80)
    ax.legend(fontsize=9)
    save(fig, "agency_framing_trend")

    # ── Figure 4: TAFS vs CSDS ────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.fill_between(YEARS, csds, alpha=0.12, color=BLUE)
    ax.plot(YEARS, csds, color=BLUE, linewidth=2.5, marker="s", markersize=8,
            zorder=4, label="CSDS — control depth")
    ax.plot(YEARS, tafs, color=GREEN, linewidth=2, marker="^", markersize=7,
            linestyle="--", label="TAFS — agency framing")
    ax.axvspan(2022.5, 2025.5, alpha=0.07, color=GREEN)
    ax.axvline(2022.5, color=AMBER, linewidth=1.2, linestyle="--", label="GenAI transition")
    style_ax(ax, "Mean TAFS (Agency Framing) vs. Mean CSDS (Control Depth) by Year",
             ylabel="Mean score")
    ax.set_xticks(YEARS)
    ax.legend(fontsize=9, framealpha=0.9)
    save(fig, "control_signal_depth_trend")

    # ── Figure 5: Agency-Control Gap A ───────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.fill_between(YEARS, gap_a, alpha=0.18, color=RED)
    ax.plot(YEARS, gap_a, color=RED, linewidth=2.5, marker="o", markersize=9, zorder=4)
    for x, y in zip(YEARS, gap_a):
        if y is not None:
            ax.text(x, y+0.8, f"{y:.0f}%", ha="center", va="bottom",
                    fontsize=9, color=RED, fontweight="bold")
    ax.axvspan(2022.5, 2025.5, alpha=0.07, color=RED)
    ax.axvline(2022.5, color=AMBER, linewidth=1.2, linestyle="--", label="GenAI transition")
    style_ax(ax, "Agency-Control Gap A: High-Agency Language with No Reported Control Signal",
             ylabel="Gap A papers (%)")
    ax.set_xticks(YEARS)
    ax.legend(fontsize=9)
    save(fig, "agency_control_gap_by_period")

    # ── Figure 6: Under-specification ────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.fill_between(YEARS, under, alpha=0.15, color=AMBER)
    ax.plot(YEARS, under, color=AMBER, linewidth=2.5, marker="D", markersize=8, zorder=4)
    corpus_avg = sum(under)/len([u for u in under if u]) if under else 0
    ax.axhline(y=corpus_avg, color=GRAY, linewidth=1.2, linestyle=":",
               label=f"Corpus avg ({corpus_avg:.0f}%)")
    ax.axvspan(2022.5, 2025.5, alpha=0.07, color=AMBER)
    ax.axvline(2022.5, color=RED, linewidth=1.2, linestyle="--", label="GenAI transition")
    style_ax(ax, "Abstract-Level Under-Specification Rate by Year",
             ylabel="Under-specified papers (%)")
    ax.set_xticks(YEARS)
    ax.legend(fontsize=9)
    save(fig, "under_specification_by_ai_type")

    # ── Figure 7: Evaluation signal robustness ────────────────────────
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(YEARS, esrs, color=NAVY, linewidth=2.5, marker="o", markersize=8, zorder=4)
    ax.axhline(y=np.mean(esrs) if esrs else 0, color=GRAY, linewidth=1,
               linestyle=":", label=f"Period mean")
    ax.axvspan(2022.5, 2025.5, alpha=0.07, color=GREEN)
    ax.axvline(2022.5, color=AMBER, linewidth=1.2, linestyle="--", label="GenAI transition")
    style_ax(ax, "Mean Evaluation Signal Robustness Score (ESRS-8) by Year",
             ylabel="Mean ESRS-8")
    ax.set_xticks(YEARS)
    ax.set_ylim(0, 8)
    ax.legend(fontsize=9)
    save(fig, "evaluation_signal_robustness")

    print(f"  All figures written to {OUT}")
    print("  Done.")


if __name__ == "__main__":
    main()
