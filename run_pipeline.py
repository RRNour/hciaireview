"""
run_pipeline.py
================
Single entry point for the AI-HCI Tiered Automated Evidence Map pipeline.
Executes all 22 steps in order. Every step is idempotent.

Usage
-----
  python run_pipeline.py --config config/config.yaml
  python run_pipeline.py --config config/config.yaml --skip-collect
  python run_pipeline.py --config config/config.yaml --from-step 6
  python run_pipeline.py --config config/config.yaml --dry-run
  python run_pipeline.py --config config/config.yaml --steps 14 15 17

Options
-------
  --config PATH          Config file (default: config/config.yaml)
  --skip-collect         Skip step 01 (use archived data)
  --skip-fulltext        Skip step 10 (skip OA retrieval)
  --from-step N          Resume from step N (1-21)
  --to-step N            Stop after step N
  --steps N [N ...]      Run specific steps only
  --dry-run              Print steps without executing
  --log-level LEVEL      DEBUG / INFO / WARNING (default: INFO)
"""

import argparse, importlib.util, logging, sys, time, yaml
from pathlib import Path


PIPELINE_STEPS = [
    ( 0, "00_setup_project",                     "Setup — validate environment and create directory structure"),
    ( 1, "01_collect_metadata",                  "Collect — retrieve records from OpenAlex API"),
    ( 2, "02_normalize_records",                 "Normalize — flatten schema and clean fields"),
    ( 3, "03_deduplicate_records",               "Deduplicate — DOI exact match + fuzzy title similarity"),
    ( 4, "04_filter_ai_hci_records",             "Filter — apply AI+HCI relevance filter + polysemy filter"),
    ( 5, "05_classify_ai_type",                  "Classify — assign dominant AI type per paper"),
    ( 6, "06_detect_agency_framing",             "Detect — TAFS agency framing score (0–5)"),
    ( 7, "07_detect_control_signals_abstract",   "Detect — CSDS control depth + CSS specificity (abstract)"),
    ( 8, "08_detect_evaluation_signals_abstract","Detect — ESRS-8 evaluation signal score (abstract)"),
    ( 9, "09_select_deep_enrichment_subset",     "Select — Layer C deep-enrichment subset (automated scoring)"),
    (10, "10_retrieve_open_fulltext",            "Retrieve — open-access full text (legal sources only)"),
    (11, "11_parse_sections",                    "Parse — heuristic section detection and quality check"),
    (12, "12_detect_control_signals_sections",   "Detect — CSDS/CSS at section level; Gap C/D resolution"),
    (13, "13_detect_evaluation_signals_sections","Detect — ESRS-8 at section level"),
    (14, "14_compute_indices",                   "Compute — merge L1/L3 scores; EDS; gap flags; under-spec"),
    (15, "15_confidence_uncertainty_depth",      "Score — confidence labels; uncertainty report"),
    (16, "16_keyword_topic_networks",            "Analyse — keyword frequencies, bigrams, TF-IDF, co-word net"),
    (17, "17_statistical_analysis",              "Analyse — all pre-specified statistical tests + sensitivity"),
    (18, "18_generate_figures",                  "Generate — all manuscript figures (PNG, 150 DPI)"),
    (19, "19_generate_prisma_counts",            "Generate — PRISMA-like flow counts and diagram"),
    (20, "20_generate_reports",                  "Report — markdown summary reports for all pipeline stages"),
    (21, "21_export_open_science_package",       "Export — validate and manifest all open-science artefacts"),
]


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def run_script(script_name: str, scripts_dir: Path) -> bool:
    """Import and run a pipeline script's main() function."""
    script_path = scripts_dir / f"{script_name}.py"
    if not script_path.exists():
        logging.error(f"Script not found: {script_path}")
        return False
    spec = importlib.util.spec_from_file_location(script_name, script_path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if hasattr(mod, "main"):
        mod.main()
    return True


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="AI-HCI Evidence Map Pipeline")
    p.add_argument("--config",       default="config/config.yaml")
    p.add_argument("--skip-collect", action="store_true")
    p.add_argument("--skip-fulltext",action="store_true")
    p.add_argument("--from-step",    type=int, default=0)
    p.add_argument("--to-step",      type=int, default=21)
    p.add_argument("--steps",        type=int, nargs="+")
    p.add_argument("--dry-run",      action="store_true")
    p.add_argument("--log-level",    default="INFO")
    return p.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s  %(levelname)s  %(message)s",
        datefmt="%H:%M:%S",
    )

    cfg = load_config(args.config)
    scripts_dir = Path("scripts")

    print("\n" + "="*70)
    print("  AI-HCI Tiered Automated Evidence Map — Pipeline Runner")
    print("="*70)
    print(f"  Config     : {args.config}")
    print(f"  Dry run    : {args.dry_run}")
    print(f"  Steps      : {args.steps or f'{args.from_step}–{args.to_step}'}")
    print("="*70 + "\n")

    skip_steps = set()
    if args.skip_collect:
        skip_steps.add(1)
        logging.info("--skip-collect: step 01 (collect_metadata) will be skipped")
    if args.skip_fulltext:
        skip_steps.add(10)
        logging.info("--skip-fulltext: step 10 (retrieve_open_fulltext) will be skipped")

    step_set = set(args.steps) if args.steps else None

    total_start = time.time()
    results = {}

    for step_num, script_name, description in PIPELINE_STEPS:
        # Step selection logic
        if step_set is not None and step_num not in step_set:
            continue
        if step_set is None and (step_num < args.from_step or step_num > args.to_step):
            continue
        if step_num in skip_steps:
            logging.info(f"  SKIP  Step {step_num:02d}: {description}")
            results[step_num] = "skipped"
            continue

        print(f"\n{'─'*70}")
        print(f"  Step {step_num:02d}: {description}")
        print(f"{'─'*70}")

        if args.dry_run:
            print(f"  [DRY RUN] Would execute: scripts/{script_name}.py")
            results[step_num] = "dry_run"
            continue

        t0 = time.time()
        try:
            ok = run_script(script_name, scripts_dir)
            elapsed = time.time() - t0
            if ok:
                logging.info(f"  ✓  Step {step_num:02d} completed in {elapsed:.1f}s")
                results[step_num] = "success"
            else:
                logging.error(f"  ✗  Step {step_num:02d} FAILED after {elapsed:.1f}s")
                results[step_num] = "failed"
        except Exception as e:
            elapsed = time.time() - t0
            logging.error(f"  ✗  Step {step_num:02d} ERROR: {e}")
            results[step_num] = f"error: {e}"

    total_elapsed = time.time() - total_start
    print("\n" + "="*70)
    print(f"  Pipeline complete in {total_elapsed:.1f}s")
    print("="*70)

    n_ok   = sum(1 for v in results.values() if v == "success")
    n_fail = sum(1 for v in results.values() if "fail" in str(v) or "error" in str(v))
    n_skip = sum(1 for v in results.values() if v in ("skipped","dry_run"))
    print(f"  Succeeded : {n_ok}")
    print(f"  Skipped   : {n_skip}")
    print(f"  Failed    : {n_fail}")

    if n_fail:
        print("\n  FAILED STEPS:")
        for step_num, status in results.items():
            if "fail" in str(status) or "error" in str(status):
                print(f"    Step {step_num:02d}: {status}")
        sys.exit(1)

    print("\n  Primary output:")
    print("    outputs/open_data/ai_hci_evidence_map_open_data.csv")
    print("\n  NEXT STEP: Deposit to Zenodo before submission.")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
