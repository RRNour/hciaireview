# Codebook
## AI-HCI Tiered Automated Evidence Map
### Author: Redhwan Nour · Taibah University

---

## Overview

This codebook defines all scoring variables, classification rules, and thresholds
used in the automated evidence mapping pipeline. All rules are operationalised in
`config/scoring_rules.yaml` and the specific term dictionaries in `config/`.

---

## Variable 1: AI Type Classification

**Variable name:** `ai_type`  
**Type:** Categorical  
**Priority order (first match wins):**

1. **agentic_ai** — agent, agentic, autonomous agent, LLM agent, multi-step, tool use, planning agent
2. **llm** — large language model, LLM, GPT, ChatGPT, language model
3. **generative** — generative AI, diffusion, image generation, text generation, DALL-E, Stable Diffusion
4. **copilot** — copilot, co-pilot, coding assistant
5. **conversational** — chatbot, conversational agent, dialogue system, virtual assistant
6. **xai** — explainable AI, XAI, interpretable ML, LIME, SHAP, saliency
7. **adaptive** — adaptive system, personalization, recommendation system
8. **classical_ml** — machine learning, neural network, deep learning (without above flags)
9. **unclassified** — no AI type terms detected

---

## Variable 2: TAFS — Textual Agency Framing Score

**Variable name:** `tafs_final`  
**Type:** Ordinal, 0–5  
**High-agency binary flag:** TAFS ≥ 3

| Score | Label | Example trigger terms | Example abstract phrase |
|---|---|---|---|
| 0 | Passive user | user, participant, recipient | "The system provides recommendations to users" |
| 1 | Decision-maker | decide, choose, select, final decision | "Users make the final decision from AI options" |
| 2 | Corrector | edit, correct, feedback, adjust | "Users can edit AI-generated suggestions" |
| 3 | Supervisor | supervise, monitor, approve, oversight, HITL | "Human supervisors approve AI actions before execution" |
| 4 | Collaborator | collaborate, co-create, copilot, jointly | "Users collaborate with the AI to co-author documents" |
| 5 | Trainer/Auditor | train, audit, govern, contest, label | "Users audit and contest AI decisions through an accountability log" |

**Scoring rule:** Assign the HIGHEST score triggered by any term in the abstract.  
**Tie-breaking:** More specific/actionable term takes precedence.

---

## Variable 3: CSDS — Control Signal Depth Score

**Variable name:** `csds_final`  
**Type:** Ordinal, 0–5

| Score | Control type | Example abstract phrase |
|---|---|---|
| 0 | No control signal | "The agent autonomously completes tasks" |
| 1 | Input/prompt control | "Users configure the AI via natural language prompts" |
| 2 | Output edit/select | "Users can select from three AI-generated alternatives" |
| 3 | Iterative steering | "Through multi-turn dialogue, users iteratively refine AI outputs" |
| 4 | Approval/override | "Human approval is required before any AI action is executed" |
| 5 | Contestability/audit | "Users can contest AI decisions via a logged appeal mechanism" |

---

## Variable 4: CSS — Control Specificity Score

**Variable name:** `css_final`  
**Type:** Ordinal, 0–3

| Score | Description | Example |
|---|---|---|
| 0 | No control language | "The AI generates content for users" |
| 1 | Vague control | "Users can control the AI's outputs" |
| 2 | Generic action | "Users can edit, reject, or regenerate outputs" |
| 3 | Named specific mechanism | "Users click 'Override' to reject; an undo button reverts last AI action" |

---

## Variable 5: ESRS — Evaluation Signal Robustness Score

**Variable name:** `esrs_final`  
**Type:** Integer, 0–8 (one point per dimension)

| Dimension | Question | Example positive indicator |
|---|---|---|
| E1 | Empirical evaluation present? | "We conducted a user study" |
| E2 | Human participants or user data? | "N=24 participants" |
| E3 | Real task or domain? | "Tax form completion task" |
| E4 | Target users specified? | "Novice programmers" |
| E5 | Baseline or comparison? | "Compared to GPT-4 baseline" |
| E6 | Quantitative/statistical analysis? | "t-test, p<0.05" |
| E7 | Qualitative analysis? | "Thematic analysis of interviews" |
| E8 | Failure analysis or usability metric? | "Error rate, task abandonment" |

---

## Variable 6: Gap A (Agency-Control Gap)

**Variable name:** `gap_a_final`  
**Type:** Binary (0/1)  
**Definition:** `TAFS >= 3 AND CSDS == 0`  
**Interpretation:** Paper uses high-agency language but reports no concrete user control mechanism in its abstract.

### Worked example — Gap A = 1
> *"We present AgentAssist, an agentic AI collaborator that autonomously plans, decomposes, and executes complex multi-step workflows on behalf of the user."*
- TAFS = 4 (collaborator)
- CSDS = 0 (no control mechanism described)
- **Gap A = 1**

### Worked example — Gap A = 0
> *"We present AgentAssist, an agentic AI collaborator. Users can pause, redirect, or reject any planned step before execution via a step-confirmation panel."*
- TAFS = 4 (collaborator)
- CSDS = 4 (approval/override)
- **Gap A = 0**

---

## Variable 7: Under-Specification

**Variable name:** `under_specified_final`  
**Type:** Binary (0/1)  
**Definition:** `TAFS >= 3 AND CSS <= 1 AND no_l3_clarifying_evidence`  
**Interpretation:** Abstract-level under-specification — high-agency language without specific reported control mechanisms.

---

## Variable 8: Evidence Depth Score

**Variable name:** `evidence_depth_label`  
**Type:** Categorical (L0, L1, L2, L3)

| Level | Source |
|---|---|
| L0 | Metadata only (title, year, venue, authors) |
| L1 | Title + abstract + keywords |
| L2 | Abstract + snippets/introduction/conclusion |
| L3 | Open-access full text / parsed sections |

---

## Supplementary Table A — Worked Examples

### TAFS Worked Examples

**Paper A (TAFS = 4, Collaborator):**  
Abstract: *"We present a co-creative writing tool in which the user collaborates with an LLM to generate story drafts, with the AI suggesting continuations and the human steering narrative direction."*  
→ Trigger: "collaborates" → TAFS = 4 ✓

**Paper B (TAFS = 2, Corrector):**  
Abstract: *"Users can edit AI-generated code suggestions before committing them to the repository."*  
→ Trigger: "edit" + output context → TAFS = 2 ✓

**Paper C (TAFS = 0, Passive user):**  
Abstract: *"The system provides personalized movie recommendations to users based on viewing history."*  
→ No active agency trigger → TAFS = 0 ✓

### CSDS Worked Examples

**Paper D (CSDS = 5, Contestability):**  
Abstract: *"Users can appeal AI-generated clinical decisions through a structured audit log and rollback mechanism that preserves the decision trace."*  
→ Triggers: "appeal", "audit log", "rollback" → CSDS = 5 ✓

**Paper E (CSDS = 2, Edit/Select):**  
Abstract: *"The interface allows users to select from three AI-generated recipe suggestions."*  
→ Trigger: "select" from AI output → CSDS = 2 ✓

**Paper F (CSDS = 0, No control):**  
Abstract: *"The AI agent autonomously completes multi-step data analysis tasks on behalf of the user, optimizing for efficiency."*  
→ No user control mechanism described → CSDS = 0 ✓

### Gap A Worked Example

**Paper G (Gap A = 1):**  
Abstract: *"We present an agentic AI co-pilot that collaborates with users to manage complex enterprise workflows, autonomously scheduling, delegating, and executing subtasks."*  
→ TAFS = 4 (collaborates), CSDS = 0 (no control reported) → **Gap A = 1** ✓

### CSS Worked Examples

**Paper H (CSS = 3, Named mechanism):**  
Abstract: *"Users click an 'Override' button to reject any AI recommendation; a confirmation dialogue prevents accidental rejections."*  
→ Named mechanism: 'Override' button → CSS = 3 ✓

**Paper I (CSS = 1, Vague):**  
Abstract: *"The system gives users full control over the AI's creative outputs, allowing them to guide the generation process."*  
→ "control" present but no mechanism specified → CSS = 1 ✓

---

## Polysemy Filter

The word "control" is excluded from CSDS/CSS scoring when it appears within a 5-token window of:

```
control group, control condition, controlled experiment, controlled study,
control variable, control arm, control baseline, statistical control,
control trial, controlled trial, randomized control, control participant
```

**Evaluated on 60-abstract sample:** precision 94%, recall 96%.  
Borderline cases ("quality control", "process control") are manually reviewed.

---

## Version

Codebook version: 1.0  
Last updated: July 2025  
Contact: rnour@taibahu.edu.sa
