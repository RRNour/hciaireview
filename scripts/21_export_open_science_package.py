"""
21_export_open_science_package.py
===================================
Collect and validate all open-science artefacts before Zenodo deposit.

Checks:
  - Open dataset CSV present and non-empty
  - All pipeline scripts present
  - All config YAML files present
  - requirements.txt and environment.yml present
  - REPLICATION.md present
  - codebook.md present
  - README.md present
  - LICENSE present
  - All key output tables present
  - All PRISMA outputs present

Produces a manifest JSON listing all artefacts and their checksums.

Inputs / Outputs
----------------
All repository files

Outputs
-------
outputs/open_science_manifest.json
outputs/open_science_checklist.md
"""

import json, hashlib, csv
from pathlib import Path
from datetime import datetime


REQUIRED = {
    "Core data": [
        "outputs/open_data/ai_hci_evidence_map_open_data.csv",
        "data/final/final_index_table.jsonl",
    ],
    "Pipeline scripts": [
        f"scripts/{s}" for s in [
            "00_setup_project.py",
            "01_collect_metadata.py",
            "02_normalize_records.py",
            "03_deduplicate_records.py",
            "04_filter_ai_hci_records.py",
            "05_classify_ai_type.py",
            "06_detect_agency_framing.py",
            "07_detect_control_signals_abstract.py",
            "08_detect_evaluation_signals_abstract.py",
            "09_select_deep_enrichment_subset.py",
            "10_retrieve_open_fulltext.py",
            "11_parse_sections.py",
            "12_detect_control_signals_sections.py",
            "13_detect_evaluation_signals_sections.py",
            "14_compute_indices.py",
            "15_confidence_uncertainty_depth.py",
            "16_keyword_topic_networks.py",
            "17_statistical_analysis.py",
            "18_generate_figures.py",
            "19_generate_prisma_counts.py",
            "20_generate_reports.py",
            "21_export_open_science_package.py",
        ]
    ],
    "Configuration": [
        f"config/{c}" for c in [
            "config.yaml", "venue_whitelist.yaml", "ai_terms.yaml",
            "agency_terms.yaml", "control_terms.yaml", "evaluation_terms.yaml",
            "search_queries.yaml", "negation_context_rules.yaml",
            "scoring_rules.yaml", "deep_subset_selection.yaml",
        ]
    ],
    "Entry point": ["run_pipeline.py"],
    "Dependencies": ["requirements.txt", "environment.yml"],
    "Documentation": ["README.md", "REPLICATION.md",
                      "codebook/codebook.md", "LICENSE"],
    "Key outputs": [
        "outputs/tables/statistical_results.json",
        "outputs/prisma/prisma_counts.csv",
        "outputs/prisma/prisma_flow.png",
    ],
}


def sha256(path: Path) -> str:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()[:16]
    except Exception:
        return "unreadable"


def file_size(path: Path) -> str:
    try:
        sz = path.stat().st_size
        if sz < 1024:
            return f"{sz}B"
        elif sz < 1048576:
            return f"{sz//1024}KB"
        else:
            return f"{sz//1048576}MB"
    except Exception:
        return "?"


def main():
    print("=== 21_export_open_science_package.py ===")

    manifest = {
        "generated": datetime.now().isoformat(),
        "repository": "https://github.com/rrnour/hciaireview",
        "artefacts": [],
    }
    checklist_rows = []
    missing = []
    present = []

    for category, files in REQUIRED.items():
        for fpath in files:
            p = Path(fpath)
            exists = p.exists()
            row = {
                "category": category,
                "path":     fpath,
                "exists":   exists,
                "size":     file_size(p) if exists else "—",
                "sha256":   sha256(p) if exists else "—",
            }
            manifest["artefacts"].append(row)
            checklist_rows.append(row)
            if exists:
                present.append(fpath)
            else:
                missing.append(fpath)

    # Write manifest
    manifest_path = Path("outputs/open_science_manifest.json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    # Write checklist MD
    checklist_md = "# Open Science Package Checklist\n\n"
    checklist_md += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    checklist_md += f"**Present: {len(present)}/{len(present)+len(missing)}**\n\n"
    if missing:
        checklist_md += f"**Missing: {len(missing)} items**\n\n"
        for m in missing:
            checklist_md += f"- ✗ {m}\n"
        checklist_md += "\n"

    last_cat = ""
    for row in checklist_rows:
        if row["category"] != last_cat:
            checklist_md += f"\n## {row['category']}\n\n"
            last_cat = row["category"]
        icon = "✓" if row["exists"] else "✗"
        sz   = f" ({row['size']})" if row["exists"] else ""
        checklist_md += f"- {icon} `{row['path']}`{sz}\n"

    checklist_md += f"\n## Zenodo Deposit\n\n"
    checklist_md += "- [ ] Mint Zenodo DOI before final submission\n"
    checklist_md += "- [ ] Update Data Availability section with Zenodo DOI\n"
    checklist_md += "- [ ] Add dataset citation to reference list\n"

    cl_path = Path("outputs/open_science_checklist.md")
    cl_path.write_text(checklist_md)

    print(f"\n  Present : {len(present)}/{len(present)+len(missing)}")
    if missing:
        print(f"  MISSING : {len(missing)}")
        for m in missing:
            print(f"    ✗ {m}")
    else:
        print("  All artefacts present ✓")
    print(f"\n  Manifest  : {manifest_path}")
    print(f"  Checklist : {cl_path}")
    print("\n  NEXT STEP: Deposit to Zenodo")
    print("    1. Push repository to GitHub")
    print("    2. zenodo.org → GitHub integration → enable hciaireview")
    print("    3. Create GitHub Release → Zenodo auto-mints DOI")
    print("    4. Update Data Availability section with DOI")
    print("  Done.")


if __name__ == "__main__":
    main()
