#!/usr/bin/env python3
"""
Script 01 — Collect Metadata from OpenAlex API
================================================
Queries the OpenAlex API for papers from the 11 core HCI venues
listed in config/venue_whitelist.yaml, filtering by publication year.

Outputs:
    data/raw/openalex_records.jsonl  — one JSON record per line

Usage:
    python scripts/01_collect_metadata.py --config config/config.yaml
"""
import argparse, json, time, os
import urllib.request, urllib.parse
import yaml

def load_config(path):
    with open(path) as f:
        return yaml.safe_load(f)

def load_venues(path="config/venue_whitelist.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)

def openalex_get(url, email, sleep=0.5):
    """Polite GET request to OpenAlex with rate-limit sleep."""
    sep = "&" if "?" in url else "?"
    url = f"{url}{sep}mailto={email}"
    req = urllib.request.Request(url, headers={"User-Agent": f"mailto:{email}"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    time.sleep(sleep)
    return data

def collect_works_for_venue(source_id, years, cfg):
    """Paginate through OpenAlex works for a single venue+year range."""
    base = cfg["api"]["openalex_base"]
    email = cfg["api"]["polite_email"]
    sleep = cfg["api"]["rate_limit_sleep"]
    year_filter = "|".join(str(y) for y in years)
    
    records = []
    cursor = "*"
    while cursor:
        url = (f"{base}/works?filter=primary_location.source.id:{source_id},"
               f"publication_year:{year_filter}"
               f"&select=id,doi,title,abstract_inverted_index,authorships,"
               f"publication_year,primary_location,concepts,referenced_works_count"
               f"&per-page=200&cursor={cursor}")
        try:
            data = openalex_get(url, email, sleep)
        except Exception as e:
            print(f"  Warning: API error for {source_id}: {e}")
            break
        
        results = data.get("results", [])
        records.extend(results)
        meta = data.get("meta", {})
        next_cursor = meta.get("next_cursor")
        cursor = next_cursor if next_cursor else None
        print(f"  Retrieved {len(records)} records so far...")
    
    return records

def invert_abstract(inverted_index):
    """Reconstruct abstract from OpenAlex inverted index format."""
    if not inverted_index:
        return ""
    positions = {}
    for word, locs in inverted_index.items():
        for pos in locs:
            positions[pos] = word
    return " ".join(positions[i] for i in sorted(positions))

def main():
    parser = argparse.ArgumentParser(description="Collect metadata from OpenAlex")
    parser.add_argument("--config", default="config/config.yaml")
    args = parser.parse_args()
    
    cfg = load_config(args.config)
    venues = load_venues()
    years = cfg["study"]["corpus_years"]
    out_path = os.path.join(cfg["paths"]["raw"], "openalex_records.jsonl")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    all_records = []
    
    # Collect from conferences
    for venue in venues["conferences"]:
        print(f"Collecting: {venue['name']}...")
        source_id = venue.get("openalex_host_venue_id", "")
        if source_id:
            records = collect_works_for_venue(source_id, years, cfg)
            for r in records:
                r["venue_name"] = venue["name"]
                r["venue_type"] = "conference"
                # Reconstruct abstract
                if "abstract_inverted_index" in r:
                    r["abstract"] = invert_abstract(r.pop("abstract_inverted_index"))
            all_records.extend(records)
            print(f"  {venue['name']}: {len(records)} records")
    
    # Collect from journals by ISSN
    for venue in venues["journals"]:
        print(f"Collecting: {venue['name']}...")
        issn = venue.get("issn", "")
        if issn:
            source_id = f"issn:{issn}"
            records = collect_works_for_venue(source_id, years, cfg)
            for r in records:
                r["venue_name"] = venue["name"]
                r["venue_type"] = "journal"
                if "abstract_inverted_index" in r:
                    r["abstract"] = invert_abstract(r.pop("abstract_inverted_index"))
            all_records.extend(records)
            print(f"  {venue['name']}: {len(records)} records")
    
    # Write output
    with open(out_path, "w", encoding="utf-8") as f:
        for record in all_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    print(f"\nTotal records collected: {len(all_records)}")
    print(f"Saved to: {out_path}")

if __name__ == "__main__":
    main()
