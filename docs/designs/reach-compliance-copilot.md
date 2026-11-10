# Design — REACH Compliance Copilot POC (v2, post-Goldfish)

*EGM design draft v2. Elephant: pi session (Nov 10). Revised after 4-way
Goldfish review (docs/designs/review/). Status: DRAFT v2 — pending user
sign-off on §10 decisions, then ready to build.*

## 1. Purpose and success criteria

Build a working end-to-end REACH compliance check that proves, with numbers:

- a fine-tuned Qwen3 4B on a 6GB card resolves substance names to canonical
  EC numbers at **≥90% exact-match accuracy on a human-verified held-out set
  (n=200), within 5 points of the local 27B reference model on the same
  set**, with 95% confidence intervals reported for both,
- at lower latency and power per 1k calls than the 27B on the 3090
  (methodology in §7),
- with the deterministic parts (list lookup, threshold rules, report) exact,
  unit-tested, and citable,
- with **zero cloud dependency** — every LLM call in the system (training
  labels, eval, runtime) is local.

The claim, stated once and used everywhere (README, post, video):

> "The 4B resolves substance names. Python computes the obligations. The
> eval proves the resolution number. Everything runs on two local GPUs —
> no cloud."

Hardware map (locked): 3090 (24GB) serves the Qwen 27B teacher/judge and
performs the LoRA fine-tune; 1660 (6GB) serves the fine-tuned 4B Q8_0.

Obligation classification by the model is OUT of scope (was Task B; see §3).

Success = the eval table exists with the bar above met (or the claim is
shrunk per §7.4), the demo BOM produces a correct cited report, and a clean
clone runs the demo (§8.3).

Non-goals:

- no web UI (CLI + report file)
- no arbitrary messy real-world BOMs (curated demo BOM)
- no Annex XVII condition engine (flag + quote; §6)
- no registration-tier reasoning (dropped — §3.3)
- no model-based obligation labels (dropped — §3)
- no portfolio monitoring service (a list-diff script tells that story — §9 step 7)

## 2. Pipeline

```
bom.csv (name, conc_pct, volume_t, use)
   │
   ▼
[1] resolve.py      4B: name → {ec_no, cas_no, canonical_name, confidence}
   │                 confidence low → status "needs_review", row skipped to report
   │                 EC/CAS not in reach.db → "needs_review"
   ▼
[2] check.py        SQLite lookup by EC/CAS: SVHC / Annex XIV / Annex XVII
   │                 → list hits + entry metadata (entry id, dates)
   ▼
[3] obligations.py  deterministic rules (§3.3 table) → obligation labels
   ▼
[4] report.py       Markdown + JSON report: per-substance findings,
                    citations, needs_review section, summary counts,
                    plain-language summary lines (template, not model)
```

Steps 2–4 are pure Python + SQLite. Step 1 calls the local llama-server.
CLI: `python -m reach check bom.csv --db data/reach.db
--model http://127.0.0.1:8080 --out report.md` (after `pip install -e .`).
`--resolver stub` reads a parallel `bom_ids.csv` of pre-verified IDs
(build-order step 1 uses this).

Model-down behavior: connection failure → one retry → all rows
`needs_review`, report still generated, exit code 2.

BOM CSV contract: header `name,conc_pct,volume_t,use`; `use` ∈
{article, mixture, substance}; missing conc_pct allowed only for
`use=substance`; units fixed (percent, tonnes/year of the product).

## 3. The fine-tune task (one task, one adapter)

### 3.1 Task A — ID resolution (the only fine-tune task in the POC)

- input: substance name as it appears in a BOM (synonyms, minor noise)
- output: JSON `{ec_no, cas_no, canonical_name, confidence: high|medium|low}`
  — schema-enforced at inference (llama-server structured output / grammar);
  malformed JSON → one retry → `needs_review`
- confidence policy (locked): **low → needs_review; medium/high → answer**.
  Training data includes abstention examples: names with >1 plausible
  EC/CAS match in ECHA data are labeled `null` + `low`, minimum 10% of the
  training mix
- calibration metric (eval): per-band accuracy table — of items the model
  labeled low, what fraction were genuinely ambiguous; of items it answered,
  what fraction were correct

### 3.2 Training data

- name sources: ECHA synonym columns + PubChem synonyms, with a stated noise
  model (typo injection rate, casing, "EC-number-in-name" variants)
- teacher: the local Qwen 27B (ATX-Swift IQ4_XS, llama-server on the 3090)
  generates labels
- validation: emitted EC/CAS must exist in ECHA data or PubChem (existence
  gate) PLUS a human spot-check of 10% of labels; measured label accuracy is
  reported in the README
- split rule: **split first, generate second** — the 200-name held-out set
  is reserved and human-verified before any generation; dedup key is
  canonical EC number (no synonym of a held-out substance may appear in
  training)
- target: 2–5K examples

### 3.3 Deterministic rules (the source of truth)

| Rule | Condition | Label |
|---|---|---|
| SVHC communication | `use=article` AND conc_pct > 0.1 (strictly greater) | `svhc_communication` |
| SVHC monitoring | `use=article` AND conc_pct ≤ 0.1 | `svhc_monitor` |
| Authorisation | substance in Annex XIV (any use) | `authorisation_required` |
| Restriction | substance matched to an Annex XVII entry (CAS/EC join) | `restriction_flagged` + entry condition text quoted |
| Clean | no hits | `no_action` |

Dropped from v1: registration tiers (1t/10t/100t) — REACH registration
tonnage is per substance per manufacturer, aggregated across products; it is
not derivable from a product BOM row. Stated in the report as out of scope.

Stated simplifications (must appear in the report footer and the post):
SVHC duty assumed for articles only; Annex XIV grandfathering/exemptions not
evaluated; Annex XVII use-specific conditions quoted, not evaluated.

## 4. Data

- `data/reach.db` (SQLite): substances, svhc_entries, annex14_entries,
  annex17_entries — ingested. Schema documented in §8.2.
- ECHA list versions pinned in `data/VERSIONS.md` (download date + list
  version); citation date = entry's list date field, not ingest date
- C&L inventory: DEFERRED (out of POC scope; report states scope
  SVHC + XIV + XVII)
- PubChem PUG-REST: training-time only (label generation + validation)
- Demo BOM (`demos/bom_demo.csv`): 8–12 substances — 2 SVHC (one >0.1%,
  one ≤0.1%), 1 Annex XIV, 1–2 Annex XVII, several clean negatives,
  1 named ambiguous substance to demonstrate needs_review (name chosen at
  build time from the >1-match set, recorded in the BOM comment)

## 5. Training and serving

- LoRA r=16, alpha=32, Unsloth, Qwen3 4B, RTX 3090
- GGUF Q8_0 (~4.3GB); Q6_K fallback if KV pressure appears
- Serve: llama-server on RTX 1660 (dedicated), **ctx 8K** (16K does not fit
  in 6GB — the brief's "8–16K" is corrected to 8K), `--jinja`,
  **thinking mode OFF** (latency + JSON reliability)
- **Gate G1 (end of build step 3):** server starts on the 1660 with 8K ctx;
  measured VRAM recorded; 100 test resolutions run clean. If it does not
  fit: Q6_K, then the claim's hardware line changes.

## 6. Known weak points (stated up front, repeated in the post)

1. Annex XVII entries have use-specific conditions the POC does not evaluate
   — it flags the entry and quotes the condition text; the human decides.
2. Trade names are out of the demo BOM; the resolver abstains on them by
   design.
3. The accuracy number is a curated-set number (human-verified, n=200).
4. Registration tiers, C&L classification, and mixture rules are out of
   scope.
5. One adapter, one task — no task-interference risk in the POC (Task B
   dropped; it returns as a stretch goal with its own eval).

## 7. Eval harness

- `eval/run_eval.py`: held-out set (200 human-verified resolution items)
  against (a) fine-tuned 4B on 1660, (b) Qwen 27B on 3090 — both scored
  against the human-verified ground truth (this breaks the teacher=judge
  circularity: the 27B is measured too, not assumed perfect)
- protocol: warm server, 3 runs, median; temperature pinned in config for
  both; identical prompts
- outputs: exact-match accuracy + 95% CI (both models), per-band calibration
  table, latency-per-1k, power-per-1k, disagreement log
  (`eval/disagreements.jsonl`)
- cost methodology (locked, all-local): measured wall power draw per model
  (W) × time-per-1k-calls × $/kWh (tariff stated); hardware amortization
  shown as a separate optional line (1660 vs 3090 purchase price over a
  stated lifetime). The business point: the narrow task moves to the 6GB
  card, leaving the 3090/27B free for everything else
- **bar and fallback:** if the 4B misses the §1 bar → shrink the public
  claim to the measured number (the post reports the real table either way);
  one retrain attempt allowed before shrinking

## 8. Repo and reproducibility

### 8.1 Layout

```
src/reach/          pipeline package (resolve, check, obligations, report, cli)
src/reach/data/     ingest.py, fetch_echa.py (existing scripts move here)
data/               ECHA CSVs + reach.db + VERSIONS.md
eval/               harness + held-out sets + disagreements
finetune/           data generation, LoRA script, GGUF export
docs/               use-case docs + this design + review reports
demos/              demo BOM + sample report
tests/              unit tests for rules + golden report test
```

`debug_echa.py` deleted before the repo goes public.

### 8.2 Schema (documented, tested)

Tables and key columns documented in `src/reach/data/SCHEMA.md`; the
substance→Annex-XVII-entry join rule (CAS/EC) specified there; entry-id and
date-field semantics defined there.

### 8.3 Reproducibility scope (locked)

- "Clean clone → `make demo`" = the cited report, using the committed
  reach.db + the GGUF shipped as a **GitHub release asset** (not git, not LFS)
  + `--resolver stub` (no GPU needed for the stub path; GPU path documented)
- reproducing the eval numbers requires the 1660 (or any 6GB+ card) + the
  release GGUF + the cloud API key
- reproducing the fine-tune requires the 3090 + `finetune/` scripts
- pinned: Python version, dependency manifest, llama.cpp version, exact
  serve command in README

## 9. Build order

1. Deterministic core: check.py + obligations.py + report.py + tests
   (unit tests for every §3.3 rule; golden test: demo BOM in → expected
   JSON report diffed out) with `--resolver stub` → first correct cited report
2. Data generation for Task A (split-first; abstention mix; spot-check)
3. Fine-tune, export GGUF, serve on 1660 → **gate G1**
4. resolve.py against llama-server; end-to-end run on the demo BOM
5. Eval harness; three-number table; bar check (§7.4)
6. (Stretch) Task B obligation labels + summary-line model — only if step 5
   is clean and time allows
7. List-diff script (new-SVHC → affected-BOM rows) — the monitoring story
8. Demo video + Substack + LinkedIn

## 10. Decisions needing user sign-off

- **D1 — RESOLVED (user, Nov 10):** all LLM usage is local. Teacher +
  judge + reference = Qwen 27B (ATX-Swift IQ4_XS) on the 3090. No cloud
  anywhere in the system.
- **D2 — confirm the bar**: ≥90% exact-match, within 5pts of the 27B,
  n=200, CIs reported. (Goldfish-forced; was never stated.)
- **D3 — confirm Task B cut** from POC scope (stretch only). The public
  claim becomes "4B resolves names; Python computes obligations."
- **D4 — confirm registration-tier drop** (domain error: tonnage is
  per-substance-per-manufacturer, not per-BOM-row).

## Glossary (for the post; kept short here)

- **REACH** — EU chemical regulation (Registration, Evaluation,
  Authorisation, Restriction of CHemicals)
- **ECHA** — European Chemicals Agency, which maintains the lists
- **SVHC / Candidate List** — Substances of Very High Concern; >0.1% in an
  article triggers communication duties
- **Annex XIV** — substances requiring authorisation before use
- **Annex XVII** — substances restricted under specific conditions
- **C&L inventory** — classification & labelling database (deferred)
- **EC / CAS number** — canonical substance identifiers (EU / US)
- **BOM** — Bill of Materials: substance, concentration, volume
- **article** — a finished object (vs a substance or mixture)
- **GGUF / Q8_0** — quantized model format / 8-bit quantization
- **LoRA** — low-rank fine-tuning adapter
