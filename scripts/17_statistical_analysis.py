#!/usr/bin/env python3
"""
Script 10 — Statistical Analysis
==================================
Performs all pre-specified non-parametric tests:
  - Mann-Kendall trend tests on annual means (7 data points)
  - Mann-Whitney U / Kruskal-Wallis for period comparisons
    (pre-GenAI 2019-2021 vs GenAI 2023-2025)
  - Mann-Whitney U for GenAI-flag comparisons
  - Cliff's delta effect sizes for all comparisons

Note: Five regression models were specified in the analysis plan
but did not converge due to small number of annual aggregates (7),
ordinal outcome distributions, and sparse cells. Regression specs
are retained in this script in the ATTEMPTED_REGRESSIONS section
for transparency.

Outputs:
    outputs/tables/statistical_results.json
    outputs/tables/summary_statistics.csv

Dependencies: scipy, numpy (pip install scipy numpy)
"""
import argparse, json, os, csv
from collections import defaultdict
import yaml

try:
    import numpy as np
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    print("Warning: scipy/numpy not found. Install with: pip install scipy numpy")
    HAS_SCIPY = False

def cliff_delta(x, y):
    """Compute Cliff's delta between two groups."""
    if not HAS_SCIPY:
        return None, None
    x, y = list(x), list(y)
    n1, n2 = len(x), len(y)
    if n1 == 0 or n2 == 0:
        return None, None
    count = sum(1 if xi > yj else (-1 if xi < yj else 0)
                for xi in x for yj in y)
    d = count / (n1 * n2)
    mag = ("negligible" if abs(d) < 0.147 else
           "small" if abs(d) < 0.330 else
           "medium" if abs(d) < 0.474 else "large")
    return round(d, 4), mag

def mannwhitney(x, y, alpha=0.05):
    if not HAS_SCIPY or not x or not y:
        return None, None, False
    stat, p = stats.mannwhitneyu(x, y, alternative="two-sided")
    return round(float(stat), 4), round(float(p), 6), p < alpha

def kruskal(*groups):
    if not HAS_SCIPY:
        return None, None, False
    stat, p = stats.kruskal(*groups)
    return round(float(stat), 4), round(float(p), 6), p < 0.05

def mann_kendall(series):
    """Mann-Kendall trend test (manual implementation)."""
    n = len(series)
    s = sum(1 if series[j] > series[i] else (-1 if series[j] < series[i] else 0)
            for i in range(n-1) for j in range(i+1, n))
    var_s = n * (n-1) * (2*n+5) / 18
    if var_s <= 0:
        return 0, 1.0, False
    import math
    z = (s - 1) / math.sqrt(var_s) if s > 0 else (s + 1) / math.sqrt(var_s) if s < 0 else 0
    if HAS_SCIPY:
        p = 2 * (1 - stats.norm.cdf(abs(z)))
    else:
        p = 1.0
    return round(z, 4), round(p, 6), p < 0.05

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/config.yaml")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    alpha = cfg["statistics"]["alpha"]
    pre_years = set(cfg["study"]["pre_genai_years"])
    genai_years = set(cfg["study"]["genai_years"])

    # Load scored corpus
    scored_path = os.path.join(cfg["paths"]["final"], "core_corpus_scored.jsonl")
    records = []
    with open(scored_path, encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line.strip()))

    # Also load full corpus for Gap A counts (all 1,207)
    full_path = os.path.join(cfg["paths"]["final"], "core_corpus_full.jsonl")
    full_records = []
    with open(full_path, encoding="utf-8") as f:
        for line in f:
            full_records.append(json.loads(line.strip()))

    indices = ["tafs", "csds", "css", "esrs", "gap_a", "gap_b", "under_specified"]

    # Group by period
    pre_data = {idx: [] for idx in indices}
    genai_data = {idx: [] for idx in indices}

    # Gap A uses full corpus
    gap_a_pre = [1 if r.get("gap_a") else 0 for r in full_records if r.get("year") in pre_years]
    gap_a_genai = [1 if r.get("gap_a") else 0 for r in full_records if r.get("year") in genai_years]

    for rec in records:
        yr = rec.get("year")
        for idx in indices:
            val = rec.get(idx)
            if val is None:
                continue
            val = float(1 if val is True else 0 if val is False else val)
            if yr in pre_years:
                pre_data[idx].append(val)
            elif yr in genai_years:
                genai_data[idx].append(val)

    # Override gap_a with full-corpus data
    pre_data["gap_a"] = gap_a_pre
    genai_data["gap_a"] = gap_a_genai

    results = {"period_comparisons": {}, "genai_flag_comparisons": {}, "trend_tests": {}}

    # Period comparisons (Mann-Whitney U)
    for idx in indices:
        stat, p, sig = mannwhitney(pre_data[idx], genai_data[idx])
        d, mag = cliff_delta(genai_data[idx], pre_data[idx])  # positive = higher in GenAI
        results["period_comparisons"][idx] = {
            "test": "Mann-Whitney U",
            "statistic": stat, "p_value": p, "significant": sig,
            "cliff_delta": d, "magnitude": mag,
            "n_pre": len(pre_data[idx]), "n_genai": len(genai_data[idx])
        }

    # GenAI-flag comparisons
    genai_flagged = {idx: [] for idx in indices}
    non_flagged = {idx: [] for idx in indices}
    for rec in records:
        flag = rec.get("genai_flag", False)
        for idx in ["tafs", "csds", "esrs", "gap_a"]:
            val = rec.get(idx)
            if val is None:
                continue
            val = float(1 if val is True else 0 if val is False else val)
            if flag:
                genai_flagged[idx].append(val)
            else:
                non_flagged[idx].append(val)

    for idx in ["tafs", "csds", "esrs", "gap_a"]:
        stat, p, sig = mannwhitney(genai_flagged[idx], non_flagged[idx])
        d, mag = cliff_delta(genai_flagged[idx], non_flagged[idx])
        results["genai_flag_comparisons"][idx] = {
            "test": "Mann-Whitney U",
            "statistic": stat, "p_value": p, "significant": sig,
            "cliff_delta": d, "magnitude": mag
        }

    # Mann-Kendall trend tests on annual means
    by_year = defaultdict(lambda: {idx: [] for idx in indices})
    for rec in records:
        yr = rec.get("year")
        for idx in indices:
            val = rec.get(idx)
            if val is not None:
                by_year[yr][idx].append(float(1 if val is True else 0 if val is False else val))

    years_sorted = sorted(by_year.keys())
    for idx in indices:
        annual_means = [sum(by_year[yr][idx]) / len(by_year[yr][idx])
                        if by_year[yr][idx] else 0 for yr in years_sorted]
        z, p, sig = mann_kendall(annual_means)
        results["trend_tests"][idx] = {
            "test": "Mann-Kendall", "statistic": z, "p_value": p, "significant": sig,
            "annual_means": {str(yr): round(m, 4) for yr, m in zip(years_sorted, annual_means)}
        }

    # ATTEMPTED REGRESSIONS (did not converge — retained for transparency)
    results["regression_note"] = (
        "Five regression models were specified in the analysis plan: "
        "CSDS ~ year + genai_flag + agentic_flag + venue_group + evidence_depth; "
        "TAFS ~ year + genai_flag + agentic_flag + venue_group + abstract_word_count; "
        "ESRS ~ year + CSDS + CSS + genai_flag + agentic_flag + venue_group + evidence_depth; "
        "gap_a ~ year + genai_flag + agentic_flag + venue_group + abstract_word_count + evidence_depth; "
        "under_specified ~ genai_flag + agentic_flag + high_agency + year + venue_group. "
        "All five models were attempted using ordinal logistic regression (statsmodels) "
        "and did not reliably converge due to: small number of annual aggregates (n=7), "
        "ordinal outcome distributions, and sparse cells for certain AI-type combinations. "
        "Results are therefore not reported and the study relies solely on the "
        "pre-specified non-parametric tests above."
    )

    out_dir = "outputs/tables"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "statistical_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Statistical results saved: {out_path}")

if __name__ == "__main__":
    main()
