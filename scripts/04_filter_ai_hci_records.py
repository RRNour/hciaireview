#!/usr/bin/env python3
"""
Script 04 — Apply AI-Relevance Filter
=======================================
Filters deduplicated records to retain only papers matching
>=1 AI term AND >=1 HCI term in title+abstract+concepts.
Applies the polysemy filter to 'control' mentions.
Tracks filter statistics for PRISMA flow.

Input:  data/normalized/deduplicated_records.jsonl
Output: data/normalized/filtered_records.jsonl
        outputs/prisma/filter_counts.json
"""
import argparse, json, os, re
import yaml

def load_terms(config_path="config/ai_terms.yaml"):
    with open(config_path) as f:
        return yaml.safe_load(f)

def text_for_matching(record):
    parts = [record.get("title", ""), record.get("abstract", "")]
    parts += record.get("concepts", [])
    return " ".join(parts).lower()

def has_term(text, terms):
    return any(t.lower() in text for t in terms)

def apply_polysemy_filter(abstract, window=5):
    """
    Returns abstract with 'control' occurrences in experimental contexts
    replaced by a placeholder, so they don't trigger the CSDS scorer.
    Experimental context words: condition, group, variable, experiment,
    baseline, trial, arm, statistical, between-subjects, within-subjects.
    """
    exclusion_contexts = [
        "condition", "group", "variable", "experiment", "baseline",
        "trial", "arm", "statistical", "between-subjects", "within-subjects",
        "controlled study"
    ]
    tokens = abstract.split()
    filtered_tokens = []
    for i, token in enumerate(tokens):
        if re.sub(r"[^a-z]", "", token.lower()) == "control":
            start = max(0, i - window)
            end = min(len(tokens), i + window + 1)
            context = " ".join(tokens[start:end]).lower()
            if any(ctx in context for ctx in exclusion_contexts):
                filtered_tokens.append("__POLYSEMY_FILTERED__")
                continue
        filtered_tokens.append(token)
    return " ".join(filtered_tokens)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/config.yaml")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    terms = load_terms()
    ai_terms = terms["ai_terms"]
    hci_terms = terms["hci_terms"]

    in_path = os.path.join(cfg["paths"]["normalized"], "deduplicated_records.jsonl")
    out_dir = cfg["paths"]["normalized"]

    records = []
    with open(in_path, encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line.strip()))

    filtered = []
    counts = {"total_input": len(records), "has_ai_term": 0,
              "has_hci_term": 0, "passes_both": 0, "excluded_year": 0}

    exclude_year = cfg["study"].get("exclude_year", 2026)

    for rec in records:
        if rec.get("year") == exclude_year:
            counts["excluded_year"] += 1
            continue

        text = text_for_matching(rec)
        has_ai = has_term(text, ai_terms)
        has_hci = has_term(text, hci_terms)

        if has_ai:
            counts["has_ai_term"] += 1
        if has_hci:
            counts["has_hci_term"] += 1

        if has_ai and has_hci:
            counts["passes_both"] += 1
            # Apply polysemy filter to abstract
            rec["abstract_filtered"] = apply_polysemy_filter(
                rec.get("abstract", ""),
                window=cfg["scoring"]["polysemy_window_tokens"]
            )
            filtered.append(rec)

    out_path = os.path.join(out_dir, "filtered_records.jsonl")
    with open(out_path, "w", encoding="utf-8") as f:
        for rec in filtered:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    prisma_dir = "outputs/prisma"
    os.makedirs(prisma_dir, exist_ok=True)
    with open(os.path.join(prisma_dir, "filter_counts.json"), "w") as f:
        json.dump(counts, f, indent=2)

    print(f"Filter complete: {len(records)} -> {len(filtered)} records")
    print(f"  Has AI term: {counts['has_ai_term']}")
    print(f"  Has HCI term: {counts['has_hci_term']}")
    print(f"  Passes both: {counts['passes_both']}")

if __name__ == "__main__":
    main()
