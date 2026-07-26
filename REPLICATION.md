# REPLICATION.md
# Agency-Control Framework for AI-HCI Research
# Repository: https://github.com/rrnour/hciaireview

## Quick Start (Full Replication)

```bash
# 1. Clone the repository
git clone https://github.com/rrnour/hciaireview
cd hciaireview

# 2. Create environment (choose one)
pip install -r requirements.txt
# OR
conda env create -f environment.yml && conda activate ai-hci-evidence-map

# 3. Run full pipeline
python run_pipeline.py --config config/config.yaml

# 4. Run from archived data (skip live API collection)
python run_pipeline.py --config config/config.yaml --skip-collect
```

Expected runtime: 45–90 minutes (limited by OpenAlex API rate limit).
Archived dataset: outputs/open_data/ai_hci_evidence_map_open_data.csv

---

## Repository Structure

```
hciaireview/
├── run_pipeline.py              # Single entry point
├── requirements.txt             # Pinned pip dependencies
├── environment.yml              # Pinned conda environment
├── REPLICATION.md               # This file
│
├── config/
│   ├── config.yaml              # Master configuration
│   ├── venue_whitelist.yaml     # 11 core HCI venues (ISSNs + OpenAlex IDs)
│   ├── agency_terms.yaml        # TAFS trigger terms (levels 0–5)
│   ├── control_terms.yaml       # CSDS trigger terms (levels 0–5) + CSS + polysemy filter
│   ├── evaluation_terms.yaml    # ESRS trigger terms (dimensions 1–8)
│   └── ai_terms.yaml            # AI-type classification terms + HCI filter terms
│
├── scripts/
│   ├── 01_collect_metadata.py   # OpenAlex API collection
│   ├── 02_normalize_records.py  # Flat schema normalization
│   ├── 03_deduplicate_records.py# DOI + fuzzy-title deduplication
│   ├── 04_filter_ai_hci_records.py # AI+HCI relevance filter + polysemy filter
│   ├── 05_classify_ai_type.py   # AI-type classification
│   ├── 06_detect_agency_framing.py # TAFS scoring
│   ├── 07_detect_control_signals_abstract.py # CSDS + CSS scoring; Gap A, Gap B
│   ├── 08_detect_evaluation_signals_abstract.py # ESRS scoring
│   ├── 09_select_deep_enrichment_subset.py  # Final corpus + open data CSV export
│   └── 17_statistical_analysis.py  # All pre-specified non-parametric tests
│
├── codebook/
│   ├── codebook.md              # Full codebook with worked examples
│   └── supplementary_table_a.md # Three worked examples per score variable
│
├── data/
│   ├── raw/
│   │   └── openalex_records.jsonl   # Raw API output (or archived snapshot)
│   ├── normalized/              # Intermediate processing files
│   └── final/
│       ├── core_corpus_full.jsonl   # All 1,207 papers
│       └── core_corpus_scored.jsonl # 630 papers (≥75 abstract words)
│
└── outputs/
    ├── open_data/
    │   └── ai_hci_evidence_map_open_data.csv  # PRIMARY OPEN DATASET
    ├── tables/
    │   ├── statistical_results.json            # All test results + effect sizes
    │   └── polysemy_filter_audit.csv                  # 60-abstract polysemy filter judgment file
    ├── figures/                                # All manuscript figures (PNG, 150 DPI)
    └── prisma/
        └── filter_counts.json                  # PRISMA stage counts
```

---

## Scoring Reference Tables

### TAFS (Textual Agency Framing Score, 0–5)
High-agency flag: TAFS ≥ 3

| Score | Label | Key trigger terms |
|-------|-------|-------------------|
| 0 | Passive user | user, participant, recipient |
| 1 | Decision-maker | decision, decide, choose, recommend |
| 2 | Corrector | correct, edit, feedback, refine |
| 3 | Supervisor ★ | supervise, monitor, approve, oversight, human-in-the-loop |
| 4 | Collaborator ★ | collaborat*, co-creat*, co-pilot, mixed initiative |
| 5 | Trainer/Auditor ★ | train, audit, contest, govern, rollback, accountability |

★ High-agency roles (TAFS ≥ 3); these rows also define the Agency-Control Taxonomy (Table 6 in manuscript).

### CSDS (Control Signal Depth Score, 0–5)
Gap A: TAFS ≥ 3 AND CSDS = 0

| Score | Label | Key trigger terms |
|-------|-------|-------------------|
| 0 | No control signal | (absent) |
| 1 | Input/prompt control | prompt, query, input, instruct |
| 2 | Output edit/reject | edit, reject, regenerate, select |
| 3 | Iterative steering | iterative, steer, redirect, multi-turn |
| 4 | Override/approval | override, veto, approve, interrupt, halt |
| 5 | Contestability/audit | contest, audit log, rollback, undo, provenance |

### CSS (Control Specificity Score, 0–3)
Gap B: TAFS ≥ 3 AND CSS ≤ 1. Under-specified: TAFS ≥ 3 AND CSS ≤ 1 AND no L3 evidence.

| Score | Label |
|-------|-------|
| 0 | No control language |
| 1 | Vague ("users can control") |
| 2 | Generic action ("users can edit outputs") |
| 3 | Specific mechanism ("click Override button") |

### ESRS (Evaluation Signal Robustness Score, 0–8)
One point per dimension: empirical evaluation, human participants, real task/domain,
target users, baseline/comparison, quantitative analysis, qualitative analysis,
failure analysis/usability metric.

---

## Worked Examples

### TAFS Examples

**Paper A — TAFS = 4 (Collaborator, High-Agency)**
> "We present CollabDraw, a human-AI co-creation tool for collaborative
> illustration. Users and the AI jointly develop concepts through iterative
> exchange."
Triggers: "co-creation" (L4), "jointly" (L4) → TAFS = 4; high_agency = True

**Paper B — TAFS = 2 (Corrector, Not High-Agency)**
> "TutorBot provides adaptive explanations. Students can edit, accept,
> or discard suggestions."
Triggers: "edit" (L2) → TAFS = 2; high_agency = False

**Paper C — TAFS = 5 (Auditor, High-Agency)**
> "We design an AI audit interface. The system provides provenance trails,
> allows contestability, and gives users governance capabilities."
Triggers: "audit" (L5), "provenance" (L5), "contestability" (L5), "governance" (L5)
→ TAFS = 5; high_agency = True

### CSDS Examples

**Paper D — CSDS = 0 (Gap A)**
> "AgentPlan autonomously plans workflows. The agent collaborates with
> project managers to optimize resource allocation."
TAFS = 4 (collaborat*); CSDS = 0 → GAP A = True

**Paper E — CSDS = 2 (Output edit)**
> "Students can request regeneration and select from alternative formulations."
Triggers: "regeneration" (L2), "select from" (L2) → CSDS = 2

**Paper F — CSDS = 4 (Override)**
> "Clinicians can override any recommendation. The system requires
> confirmation before committing AI-generated diagnoses."
Triggers: "override" (L4), "confirmation" (L4) → CSDS = 4

### CSS Example

**Paper G — Full Gap A Example (TAFS=4, CSDS=0, CSS=0)**
> "AgentPlan, an agentic AI system that autonomously plans and executes
> project management workflows. The system collaborates with project managers."
TAFS=4 (collaborat*); CSDS=0; CSS=0
Gap A = True | Gap B = True | Under-specified = True

### ESRS Example

**Paper H — ESRS = 6**
> "We evaluate our AI writing assistant with 48 participants (n=48) in
> a real writing task using a between-subjects design. We compare against
> a no-AI baseline. Results show significant improvement (p < 0.01) in
> writing quality."
Dims: (1) evaluat*, (2) n=48, (3) real writing task, (5) baseline, (6) significant, p <
→ ESRS = 5 (dims 1,2,3,5,6 matched; 4=no target user, 7=no qualitative, 8=no failure)

**Paper I — ESRS = 7 (adds qualitative)**
Same as H but also includes: "Post-task interviews revealed..."
→ ESRS = 6 (adds dim 7)

---

## Statistical Analysis Notes

All tests performed in script 17_statistical_analysis.py using scipy.stats.

**Period comparisons** (Mann-Whitney U, two-sided):
- Pre-GenAI: 2019–2021 (n = 210 scored papers)
- GenAI: 2023–2025 (n = 342 scored papers)
- Transition year 2022 excluded from period comparisons

**GenAI-flag comparisons** (Mann-Whitney U):
- GenAI-flagged: papers with ai_type in {llm, generative_ai, copilot}
- Non-flagged: all other papers

**Trend tests** (Mann-Kendall):
- Applied to 7 annual mean values (2019–2025)
- Limited statistical power due to small series length

**Effect sizes** (Cliff's delta, Vargha & Delaney 2000):
- Period comparisons: positive δ = higher in GenAI period
- GenAI-flag comparisons: positive δ = higher in GenAI-flagged papers

**Regression models** (attempted, did not converge):
Specifications retained in script 10 under ATTEMPTED_REGRESSIONS.
See manuscript §4.6 for explanation.

---

## Data Availability

| Artefact | Location |
|----------|----------|
| Primary open dataset (1,207 records) | outputs/open_data/ai_hci_evidence_map_open_data.csv |
| Scored subset (630 records) | data/final/core_corpus_scored.jsonl |
| Statistical results | outputs/tables/statistical_results.json |
| Polysemy filter judgments | outputs/tables/polysemy_filter_audit.csv |
| Precision audit judgments | outputs/tables/precision_audit_judgments.csv |
| All figures (PNG 150 DPI) | outputs/figures/ |
| PRISMA stage counts | outputs/prisma/filter_counts.json |
| Deduplication report | data/normalized/deduplication_report.json |

Persistent archive (Zenodo DOI to be added before final publication).
