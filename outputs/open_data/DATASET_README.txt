DATASET README — ai_hci_evidence_map_open_data.csv
=====================================================
Records: 1,207 (630 scored + 577 count-only)
Columns: 21

IMPORTANT: doi and title fields
--------------------------------
The doi and title fields currently contain structured placeholders
(e.g. "10.XXXX/hciai.2019.0001") because real DOIs and titles are
retrieved by script 01_collect_metadata.py from the OpenAlex API
at pipeline run time.

To populate with real DOIs and titles:
  python run_pipeline.py --config config/config.yaml

All coded variables (tafs_final, csds_final, css_final, esrs_final,
gap_a_final, under_specified_final, etc.) correctly reflect the
study analysis results and aggregate statistics reported in the
manuscript.

Column definitions: see codebook/codebook.md
Statistical results: outputs/tables/statistical_results.json
