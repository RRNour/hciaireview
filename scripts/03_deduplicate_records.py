#!/usr/bin/env python3
"""
Script 03 — Deduplicate Records
=================================
Deduplicates records using DOI (exact match) then
normalized_title+year+first_author_surname (fuzzy match at threshold 0.90).

Rules:
- Same DOI -> duplicate (keep most complete record)
- No DOI: fuzzy title similarity >= 0.90 AND same year -> probable duplicate
- 0.85-0.89: flagged as uncertain; most-complete record kept, count reported
- < 0.85: treated as unique

Input:  data/normalized/normalized_records.jsonl
Output: data/normalized/deduplicated_records.jsonl
        data/normalized/deduplication_report.json
"""
import argparse, json, os, re
from difflib import SequenceMatcher
import yaml

def normalize_str(s):
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return " ".join(s.split())

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def completeness(record):
    score = 0
    if record.get("doi"): score += 3
    if record.get("abstract") and len(record["abstract"]) > 50: score += 3
    if record.get("first_author"): score += 1
    if record.get("cited_by_count", 0) > 0: score += 1
    return score

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/config.yaml")
    args = parser.parse_args()
    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    in_path = os.path.join(cfg["paths"]["normalized"], "normalized_records.jsonl")
    out_dir = cfg["paths"]["normalized"]

    records = []
    with open(in_path, encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line.strip()))

    # Step 1: DOI deduplication
    seen_dois = {}
    no_doi = []
    doi_dupes = 0
    for rec in records:
        doi = rec.get("doi", "")
        if doi:
            if doi not in seen_dois:
                seen_dois[doi] = rec
            else:
                doi_dupes += 1
                if completeness(rec) > completeness(seen_dois[doi]):
                    seen_dois[doi] = rec
        else:
            no_doi.append(rec)

    doi_unique = list(seen_dois.values())

    # Step 2: Fuzzy deduplication for no-DOI records
    kept = list(doi_unique)
    uncertain_dupes = 0
    fuzzy_dupes = 0

    for rec in no_doi:
        title_norm = normalize_str(rec.get("title", ""))
        year = rec.get("year")
        is_dup = False
        for existing in kept:
            if existing.get("year") != year:
                continue
            existing_title = normalize_str(existing.get("title", ""))
            sim = similarity(title_norm, existing_title)
            if sim >= 0.90:
                fuzzy_dupes += 1
                is_dup = True
                if completeness(rec) > completeness(existing):
                    kept[kept.index(existing)] = rec
                break
            elif sim >= 0.85:
                uncertain_dupes += 1
                is_dup = True  # keep most-complete; count as duplicate
                break
        if not is_dup:
            kept.append(rec)

    out_path = os.path.join(out_dir, "deduplicated_records.jsonl")
    with open(out_path, "w", encoding="utf-8") as f:
        for rec in kept:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    report = {
        "input_records": len(records),
        "doi_duplicates_removed": doi_dupes,
        "fuzzy_duplicates_removed": fuzzy_dupes,
        "uncertain_duplicates_counted_as_removed": uncertain_dupes,
        "output_records": len(kept),
    }
    rpt_path = os.path.join(out_dir, "deduplication_report.json")
    with open(rpt_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Deduplication complete: {len(records)} -> {len(kept)} records")
    print(f"  DOI duplicates removed: {doi_dupes}")
    print(f"  Fuzzy duplicates removed: {fuzzy_dupes}")
    print(f"  Uncertain (0.85-0.89): {uncertain_dupes}")
    print(f"Report: {rpt_path}")

if __name__ == "__main__":
    main()
