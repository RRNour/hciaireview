# Reproducibility Report

Generated: 2026-07-05

## Single-Command Replication

```bash
python run_pipeline.py --config config/config.yaml
```

To use archived data (no API calls):
```bash
python run_pipeline.py --config config/config.yaml --skip-collect
```

## Pipeline Scripts (24 files)
- `scripts/00_setup_project.py`
- `scripts/01_collect_metadata.py`
- `scripts/02_normalize_records.py`
- `scripts/03_deduplicate_records.py`
- `scripts/04_filter_ai_hci_records.py`
- `scripts/05_classify_ai_type.py`
- `scripts/06_detect_agency_framing.py`
- `scripts/07_detect_control_signals_abstract.py`
- `scripts/08_detect_evaluation_signals_abstract.py`
- `scripts/09_compile_final_corpus.py`
- `scripts/09_select_deep_enrichment_subset.py`
- `scripts/10_retrieve_open_fulltext.py`
- `scripts/10_statistical_analysis.py`
- `scripts/11_parse_sections.py`
- `scripts/12_detect_control_signals_sections.py`
- `scripts/13_detect_evaluation_signals_sections.py`
- `scripts/14_compute_indices.py`
- `scripts/15_confidence_uncertainty_depth.py`
- `scripts/16_keyword_topic_networks.py`
- `scripts/17_statistical_analysis.py`
- `scripts/18_generate_figures.py`
- `scripts/19_generate_prisma_counts.py`
- `scripts/20_generate_reports.py`
- `scripts/21_export_open_science_package.py`


## Configuration Files (10 files)
- `config/agency_terms.yaml`
- `config/ai_terms.yaml`
- `config/config.yaml`
- `config/control_terms.yaml`
- `config/deep_subset_selection.yaml`
- `config/evaluation_terms.yaml`
- `config/negation_context_rules.yaml`
- `config/scoring_rules.yaml`
- `config/search_queries.yaml`
- `config/venue_whitelist.yaml`


## Dependencies
- requirements.txt (pip, all packages pinned)
- environment.yml (conda, all packages pinned)
- Python 3.9+ required

## Open Data
Primary open dataset: `outputs/open_data/ai_hci_evidence_map_open_data.csv`  
Statistical results: `outputs/tables/statistical_results.json`  
Persistent archive: Zenodo DOI to be minted before final publication.

## Notes
- Minor variation in OpenAlex API responses expected across retrieval dates
- Archived dataset provides a fixed reference snapshot
- L3 full-text retrieval results depend on open-access status at retrieval time
- All scoring thresholds in config/*.yaml — editable without touching Python
