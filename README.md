# AI-HCI Tiered Automated Evidence Map
### The Agency-Control Framework for AI-HCI Research (2019–2025)

**Paper:** "The Agency-Control Framework for AI-HCI Research: A Tiered Automated Evidence Map of Human Control, Agency, and Evaluation in AI-HCI Research, 2019–2025"  
**Author:** Redhwan Nour · Department of Information Systems · Taibah University  
**Email:** rnour@taibahu.edu.sa  
**Target journal:** PeerJ Computer Science  
**Repository:** https://github.com/rrnour/hciaireview

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/rrnour/hciaireview
cd hciaireview

# 2. Install (choose one)
pip install -r requirements.txt
# OR
conda env create -f environment.yml && conda activate ai-hci-evidence-map

# 3. Run full pipeline
python run_pipeline.py --config config/config.yaml

# 4. Run from archived dataset (no API calls)
python run_pipeline.py --config config/config.yaml --skip-collect

# 5. Resume from a specific step
python run_pipeline.py --config config/config.yaml --from-step 6

# 6. Validate environment and structure only
python scripts/00_setup_project.py
```

**Expected runtime:** 45–90 min (limited by OpenAlex API rate limits).  
**Archived dataset:** `outputs/open_data/ai_hci_evidence_map_open_data.csv`

---

## Study Design

This study is a **tiered automated evidence map** — not a manual systematic review. It combines:

- **Layer A** — Broad corpus: bibliometric and keyword trends (~3,000–8,000 records)  
- **Layer B** — Core HCI corpus: AI-HCI detection pipeline (1,000–1,500 records)  
- **Layer C** — Deep enrichment subset: automated priority-scored open-access full-text analysis (100–150 records)

---

## Variables Coded

| Variable | Description | Range |
|---|---|---|
| TAFS | Textual Agency Framing Score | 0–5 |
| CSDS | Control Signal Depth Score | 0–5 |
| CSS | Control Specificity Score | 0–3 |
| ESRS-8 | Evaluation Signal Robustness Score | 0–8 |
| EDS | Evidence Depth Score | 0–3 |
| Gap A | High-agency + no control signal | boolean |
| Gap B | High-agency + vague control only | boolean |
| Gap C | Gap A resolved by L3 evidence | boolean |
| Gap D | Gap A persistent at L3 | boolean |

---

## Repository Structure

```
hciaireview/
├── run_pipeline.py              # Single entry point (22 steps)
├── requirements.txt             # Pinned pip dependencies
├── environment.yml              # Pinned conda environment
├── README.md                    # This file
├── REPLICATION.md               # Step-by-step replication guide
├── LICENSE                      # MIT
│
├── config/                      # All scoring rules and term dictionaries
│   ├── config.yaml              # Master configuration
│   ├── search_queries.yaml      # API query terms
│   ├── venue_whitelist.yaml     # 11 core HCI venues
│   ├── ai_terms.yaml            # AI type classification terms
│   ├── agency_terms.yaml        # TAFS trigger terms (levels 0–5)
│   ├── control_terms.yaml       # CSDS/CSS trigger terms + polysemy filter
│   ├── evaluation_terms.yaml    # ESRS-8 trigger terms (8 dimensions)
│   ├── negation_context_rules.yaml
│   ├── scoring_rules.yaml       # All thresholds and point values
│   └── deep_subset_selection.yaml
│
├── scripts/
│   ├── 00_setup_project.py      # Create dirs, validate env
│   ├── 01_collect_metadata.py   # OpenAlex API collection
│   ├── 02_normalize_records.py  # Schema normalisation
│   ├── 03_deduplicate_records.py
│   ├── 04_filter_ai_hci_records.py
│   ├── 05_classify_ai_type.py
│   ├── 06_detect_agency_framing.py     # TAFS 0–5
│   ├── 07_detect_control_signals_abstract.py  # CSDS, CSS, Gap A/B
│   ├── 08_detect_evaluation_signals_abstract.py  # ESRS-8
│   ├── 09_select_deep_enrichment_subset.py   # Layer C selection
│   ├── 10_retrieve_open_fulltext.py    # OA full text (no paywall bypass)
│   ├── 11_parse_sections.py            # Section-level text parsing
│   ├── 12_detect_control_signals_sections.py  # L3 CSDS/CSS; Gap C/D
│   ├── 13_detect_evaluation_signals_sections.py
│   ├── 14_compute_indices.py           # Merge L1/L3; EDS; under-spec
│   ├── 15_confidence_uncertainty_depth.py
│   ├── 16_keyword_topic_networks.py    # TF-IDF, co-word network
│   ├── 17_statistical_analysis.py      # All inferential tests
│   ├── 18_generate_figures.py
│   ├── 19_generate_prisma_counts.py
│   ├── 20_generate_reports.py
│   └── 21_export_open_science_package.py
│
├── codebook/
│   └── codebook.md              # Scoring definitions and worked examples
│
├── data/                        # Pipeline intermediates (not committed)
└── outputs/                     # All outputs (committed)
    ├── open_data/               # PRIMARY OPEN DATASET (CSV)
    ├── tables/                  # All result tables
    ├── figures/                 # All manuscript figures (PNG, 150 DPI)
    ├── prisma/                  # PRISMA flow counts and diagram
    └── reports/                 # Markdown report files
```

---

## Open Data

| Artefact | Path |
|---|---|
| **Primary open dataset** | `outputs/open_data/ai_hci_evidence_map_open_data.csv` |
| Statistical results | `outputs/tables/statistical_results.json` |
| PRISMA counts | `outputs/prisma/prisma_counts.csv` |
| Polysemy audit | `outputs/tables/polysemy_audit.csv` |
| Precision audit | `outputs/tables/precision_audit_judgments.csv` |
| All figures | `outputs/figures/*.png` |

Persistent Zenodo DOI: *to be minted before final publication*

---

## Citation

Nour R. 2025. The Agency-Control Framework for AI-HCI Research: A Tiered Automated Evidence Map of Human Control, Agency, and Evaluation in AI-HCI Research, 2019–2025. *PeerJ Computer Science* [under review].

---

## License

MIT License — see LICENSE file.
