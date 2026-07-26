"""
10_retrieve_open_fulltext.py
=============================
Retrieve open-access full text for papers in the deep-enrichment
subset.  Only uses legal open-access sources — does NOT bypass
paywalls.

Sources tried (in order):
  1. Unpaywall API (email registered in config)
  2. OpenAlex open_access.oa_url field
  3. Semantic Scholar open access PDF URL
  4. arXiv if arXiv DOI detected

Inputs
------
data/final/deep_enrichment_subset.jsonl
config/config.yaml

Outputs
-------
data/fulltext/<doi_safe>.txt      — plain-text extraction per paper
outputs/tables/fulltext_retrieval_report.csv
"""

import json, yaml, csv, time, re, os
from pathlib import Path

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def load_config(path: str = "config/config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def doi_to_safe_filename(doi: str) -> str:
    return re.sub(r"[^\w\-]", "_", doi)[:120]


def try_unpaywall(doi: str, email: str) -> str | None:
    if not doi or not HAS_REQUESTS:
        return None
    try:
        url = f"https://api.unpaywall.org/v2/{doi}?email={email}"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            best = data.get("best_oa_location")
            if best and best.get("url_for_pdf"):
                return best["url_for_pdf"]
    except Exception:
        pass
    return None


def try_semantic_scholar(doi: str) -> str | None:
    if not doi or not HAS_REQUESTS:
        return None
    try:
        url = f"https://api.semanticscholar.org/graph/v1/paper/{doi}?fields=openAccessPdf"
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            oa = data.get("openAccessPdf")
            if oa and oa.get("url"):
                return oa["url"]
    except Exception:
        pass
    return None


def download_pdf_text(pdf_url: str) -> str | None:
    """Download PDF and extract text. Requires pdfminer or similar."""
    if not HAS_REQUESTS:
        return None
    try:
        r = requests.get(pdf_url, timeout=30, stream=True)
        if r.status_code != 200:
            return None
        # Try to parse PDF bytes
        try:
            import io
            from pdfminer.high_level import extract_text as pdf_extract
            text = pdf_extract(io.BytesIO(r.content))
            return text.strip() if text and len(text) > 200 else None
        except ImportError:
            # pdfminer not installed; return raw indicator
            return "[PDF_RETRIEVED_NO_PARSER]"
    except Exception:
        return None


def main():
    print("=== 10_retrieve_open_fulltext.py ===")
    cfg = load_config()
    email = cfg.get("unpaywall_email", "researcher@institution.edu")

    in_path  = Path("data/final/deep_enrichment_subset.jsonl")
    out_dir  = Path("data/fulltext")
    rpt_path = Path("outputs/tables/fulltext_retrieval_report.csv")
    out_dir.mkdir(parents=True, exist_ok=True)
    rpt_path.parent.mkdir(parents=True, exist_ok=True)

    records = []
    if in_path.exists():
        with open(in_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))

    print(f"  Input records : {len(records)}")
    print(f"  Unpaywall email: {email}")
    print("  NOTE: Only open-access sources used. Paywalls not bypassed.")

    report = []
    retrieved = 0

    for rec in records:
        doi  = rec.get("doi", "")
        safe = doi_to_safe_filename(doi) if doi else f"no_doi_{rec.get('_id','x')}"
        out_file = out_dir / f"{safe}.txt"

        status   = "skip_exists"
        source   = ""
        pdf_url  = ""

        if out_file.exists():
            status = "skip_exists"
        else:
            # Try sources in order
            pdf_url = try_unpaywall(doi, email)
            if pdf_url:
                source = "unpaywall"
            else:
                pdf_url = try_semantic_scholar(doi)
                if pdf_url:
                    source = "semantic_scholar"

            if pdf_url:
                text = download_pdf_text(pdf_url)
                if text and "[PDF_RETRIEVED" not in text:
                    with open(out_file, "w") as f:
                        f.write(text)
                    status = "success"
                    retrieved += 1
                elif text == "[PDF_RETRIEVED_NO_PARSER]":
                    with open(out_file, "w") as f:
                        f.write(text)
                    status = "no_parser"
                else:
                    status = "download_failed"
            else:
                status = "no_oa_url"

            time.sleep(0.5)  # Rate limiting

        report.append({
            "doi":      doi,
            "year":     rec.get("year", ""),
            "status":   status,
            "source":   source,
            "pdf_url":  pdf_url,
        })

    print(f"  Retrieved  : {retrieved}/{len(records)}")
    print(f"  OA rate    : {retrieved/len(records)*100:.1f}%" if records else "  No records")

    if report:
        with open(rpt_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(report[0].keys()))
            writer.writeheader()
            writer.writerows(report)

    print(f"  Report : {rpt_path}")
    print("  Done.")


if __name__ == "__main__":
    main()
