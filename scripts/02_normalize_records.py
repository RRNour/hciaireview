#!/usr/bin/env python3
"""
Script 02 — Normalize Records
==============================
Normalizes raw OpenAlex records to a consistent flat schema.
Extracts: doi, title, abstract, year, venue_name, venue_type,
          first_author, author_count, cited_by_count.

Input:  data/raw/openalex_records.jsonl
Output: data/normalized/normalized_records.jsonl
"""
import argparse, json, os, re
import yaml

def normalize_doi(doi):
    if not doi:
        return ""
    doi = str(doi).strip().lower()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
    return doi

def normalize_title(title):
    if not title:
        return ""
    return " ".join(str(title).strip().split())

def extract_first_author(authorships):
    if not authorships:
        return ""
    for auth in sorted(authorships, key=lambda a: a.get("author_position", 99)):
        name = auth.get("author", {}).get("display_name", "")
        if name:
            return name
    return ""

def normalize_record(raw):
    return {
        "openalex_id": raw.get("id", "").replace("https://openalex.org/", ""),
        "doi": normalize_doi(raw.get("doi", "")),
        "title": normalize_title(raw.get("title", "")),
        "abstract": (raw.get("abstract") or "").strip(),
        "year": raw.get("publication_year"),
        "venue_name": raw.get("venue_name", ""),
        "venue_type": raw.get("venue_type", ""),
        "first_author": extract_first_author(raw.get("authorships", [])),
        "author_count": len(raw.get("authorships", [])),
        "cited_by_count": raw.get("cited_by_count", 0),
        "concepts": [c.get("display_name", "") for c in raw.get("concepts", [])
                     if c.get("score", 0) >= 0.3],
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/config.yaml")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    in_path = os.path.join(cfg["paths"]["raw"], "openalex_records.jsonl")
    out_dir = cfg["paths"]["normalized"]
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "normalized_records.jsonl")

    normalized = []
    with open(in_path, encoding="utf-8") as f:
        for line in f:
            raw = json.loads(line.strip())
            norm = normalize_record(raw)
            if norm["title"]:
                normalized.append(norm)

    with open(out_path, "w", encoding="utf-8") as f:
        for record in normalized:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Normalized {len(normalized)} records -> {out_path}")

if __name__ == "__main__":
    main()
