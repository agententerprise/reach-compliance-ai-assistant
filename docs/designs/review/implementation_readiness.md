# Goldfish Review — Implementation Readiness

*Reviewer: Implementation Readiness Goldfish (EGM). Mode: REVIEW.
Inputs: `concepts_brief.md`, `docs/designs/reach-compliance-copilot.md` (DRAFT).
Zero prior context. Read-only audit.*

## Summary

The design is a coherent build specification with a sensible build order and an
honest "known weak points" section. However, it is not yet actionable for an
implementer: the two things the POC exists to prove — the fine-tune task
specification and the eval bar — are the least specified parts of the document.
Several pipeline branches are left to implementer judgment, the data schema is
referenced but never defined, and two of the brief's open questions (confidence
policy, eval bar) are carried into the design unclosed.

**Verdict: NEEDS-WORK** (details below; the deterministic core, §9 step 1, is
ready to start today).

---

## Findings

### F1. The eval bar is never stated — the POC's success criterion is unfalsifiable
- **Severity**: Blocker
- **Affected scope**: §1 ("within a small, stated margin"), §7; brief open question 5
- **Finding**: §1 promises accuracy "within a small, stated margin of a cloud
  big LLM." The margin is never stated. §7 lists outputs (accuracy, abstention
  calibration, cost, latency) but defines no acceptance threshold, no
  statistical test, and no rule for what happens if the 4B misses the bar
  (retrain? shrink the claim? change the task set?). "The eval table exists and
  is honest" is not a testable success criterion.
- **Guidance**: State the bar explicitly (e.g., "Task A exact-match within 5
  points of the cloud model on the held-out set, with abstention counted as
  correct per §3 Task A"), name the cloud model (see F2), and define the
  fallback decision if the bar is missed.

### F2. "Cloud big LLM" is never named
- **Severity**: Blocker
- **Affected scope**: §3 (teacher labels), §7 (eval reference), brief
- **Finding**: The teacher model, the eval judge, and the cost/latency
  comparison target are all "a cloud big LLM." Cost-per-1k and
  latency-per-1k are meaningless without a named model and API. Reproducibility
  ("repo is reproducible from a clean clone", §1) is broken: a re-runner cannot
  reproduce the comparison column.
- **Guidance**: Name the model, provider, and API version in §5/§7. Pin it in
  the eval harness config.

### F3. Task A and Task B have no prompt/response specification
- **Severity**: Blocker
- **Affected scope**: §3 (both tasks), §5
- **Finding**: "Input: substance name as it appears in a BOM" and "output:
  JSON {…}" are data-shape descriptions, not a task specification. The
  implementer must independently decide: the instruction template, the system
  prompt, how the two tasks are disambiguated in a single adapter (presumably
  by prompt, but unstated), whether llama-server enforces the JSON schema
  (grammar/structured output) or the pipeline parses free text, and what
  happens on malformed JSON (retry? needs_review? crash?). For a fine-tune,
  the training prompt template *is* the spec — it is missing.
- **Guidance**: Add the exact prompt templates for both tasks, the JSON schema
  enforced at inference (llama-server supports structured output), and the
  malformed-response policy (e.g., one retry, then status `needs_review`).

### F4. Confidence policy is undefined for the `medium` band
- **Severity**: Major
- **Affected scope**: §2 step 1, §3 Task A; brief open question 1
- **Finding**: The model emits `high|medium|low`, but the pipeline only
  branches on "low confidence → needs_review." Is `medium` treated as
  resolved? If so, the abstention feature (brief Q1) is half-implemented and
  the eval's "abstention calibration" metric (§7) has no defined operating
  point. Also: self-reported confidence from a 4B is uncalibrated by default —
  the design never says how confidence is trained (what labels make an example
  "low"?) or measured.
- **Guidance**: Decide and write down: which confidence bands trigger
  `needs_review`, how confidence labels are generated in training data, and
  the exact abstention-calibration metric (e.g., accuracy-within-band table).

### F5. Training-data generation spec is too thin to execute
- **Severity**: Major
- **Affected scope**: §3 Task A labels, §5 ("~2–5K examples, generated,
  validated, deduplicated")
- **Finding**: Unspecified: the name source (ECHA synonym columns? PubChem
  synonyms? synthetic noise?), the teacher prompt, the Task A / Task B split of
  the 2–5K budget, the dedup key, and — critically — when the held-out sets
  (§7: ≥200 resolution, ≥100 obligation items) are carved out. If held-out
  names are not reserved *before* generation, synonym leakage (a training
  synonym of a substance whose other synonym is in the eval set) inflates
  accuracy and the headline number is compromised.
- **Guidance**: Add a data-generation section: name sources, teacher prompt,
  per-task example counts, dedup key (canonical EC/CAS), and an explicit
  "split first, generate second" rule with leakage definition.

### F6. Label validation drops exactly the examples the abstention feature needs
- **Severity**: Major
- **Affected scope**: §3 Task A ("invalid labels dropped"), §6.2
- **Finding**: "The emitted EC/CAS must exist in the ECHA data or PubChem;
  invalid labels dropped." Names with no valid resolution (trade names,
  genuinely ambiguous names) produce dropped examples. The training set then
  contains almost no "correct answer is: abstain" examples, so the model is
  unlikely to emit `low` confidently — directly contradicting §6.2's claim
  that abstention "is the designed behavior."
- **Guidance**: Define how abstention examples are constructed (e.g., teacher
  labels of `null` + `low` for names with >1 plausible match) and include a
  stated minimum fraction in the training mix.

### F7. SQLite schema is "done" but undocumented
- **Severity**: Major
- **Affected scope**: §4, §2 steps 2–3, citations in §2 step 5
- **Finding**: The design references `substances, svhc_entries,
  annex14_entries, annex17_entries` and requires citations of "list, entry ID,
  date," but no table definitions, column names, entry-ID format, or date
  semantics (list publication date? entry addition date?) appear anywhere.
  The implementer must reverse-engineer `data/reach.db`. Also unspecified: how
  Annex XVII entries are matched to substances (entry→substance mapping table?
  CAS join?) — §2 step 3 says "entry matched → flag" as if the matching
  mechanism is obvious.
- **Guidance**: Add a schema section (tables, key columns, entry-ID and date
  semantics) and the substance→Annex-XVII-entry join rule.

### F8. The deterministic rules are not actually fully specified
- **Severity**: Major
- **Affected scope**: §2 step 3, §1 ("deterministic parts … exact and citable")
- **Finding**: Three gaps in the "source of truth" rules:
  1. "Registration tiers: 1t/10t/100t by volume" — REACH registration
     tonnage is per-substance per-manufacturer; the BOM's `volume_t` is
     product volume. The rule silently conflates the two. State the
     simplification explicitly (it is a POC simplification, and the report
     must say so).
  2. "SVHC: conc > 0.1% in article" — what if `use` is a mixture, not an
     article? The `use` column's allowed values are never defined.
  3. Boundary semantics: is 0.1% exactly a hit (`>` vs `>=`)? 1t exactly?
- **Guidance**: Enumerate the rule table with boundary semantics, the allowed
  `use` values, and the stated simplifications. This section needs unit tests
  (see F11).

### F9. CLI and report contracts are underspecified
- **Severity**: Major
- **Affected scope**: §2 (CLI line), §2 step 5, §9 step 1
- **Finding**: No output path argument (where does the report land?), no exit
  code contract, no behavior when llama-server is down (fail? degrade to
  needs_review for every row?), and no BOM CSV contract (header names, units,
  missing values, a substance with no concentration). §9 step 1 requires a
  "stub resolver (pre-verified IDs)" but the wiring is unspecified
  (`--resolver stub`? a separate BOM file of IDs?). The JSON report has no
  schema; the Markdown report has no template.
- **Guidance**: Specify the full CLI signature, the BOM CSV contract, the
  stub-resolver mechanism, the model-down behavior, and at least a field list
  for the JSON report.

### F10. Task B's runtime role is self-contradictory
- **Severity**: Major
- **Affected scope**: §2 step 4, §3 Task B
- **Finding**: Step 4 is "(4B, optional) obligation label refinement."
  Optional for whom, decided when? §3 says the deterministic rules are the
  source of truth, the report cites the rules "not the model," and
  model/rule disagreement "is an eval signal, not a runtime branch." If the
  model's labels never affect the report, step 4's only runtime output is the
  plain-language summary line — say so, and specify that the summary line is
  the sole runtime use of Task B (and what happens to it when Task B is
  dropped per §6.4). As written, the implementer must decide what step 4 does.
- **Guidance**: Rewrite step 4 as: "4B generates the plain-language summary
  line only; labels are eval-only." Define the summary-line prompt and its
  failure mode (model down → omit the line).

### F11. No test plan for the deterministic core
- **Severity**: Major
- **Affected scope**: §1 ("exact and citable"), §9 step 1
- **Finding**: The credibility claim of the whole POC is that the
  deterministic parts are exact. There is no test section anywhere: no unit
  tests for the threshold rules, no fixture BOM with expected report output,
  no definition of what "first correct cited report" (build order step 1)
  means verifiably.
- **Guidance**: Add: unit tests for every rule in F8's table, and a golden
  test — demo BOM in, expected report (or its JSON) diffed out.

### F12. Reproducibility claims outrun the repo spec
- **Severity**: Major
- **Affected scope**: §1, §5, §8
- **Finding**: "Reproducible from a clean clone" requires: Python version,
  dependency manifest (none in §8), llama.cpp version, GGUF filename,
  llama-server launch command/flags (port 8080 is assumed in §2; ctx 8K in
  §5; sampling parameters absent), and the fine-tune seed/config. None are
  specified. The 1660 (6GB) + Q8_0 (~4.3GB) + 8K ctx KV cache fit is asserted,
  not verified — state the measured `llama-server` startup as a checkpoint.
- **Guidance**: Add a "runtime environment" section: pinned deps, llama.cpp
  version, exact serve command, and a smoke-check step in build order
  ("server starts on 1660 with 8K ctx; record VRAM").

### F13. Cost model for the local model is undefined
- **Severity**: Major
- **Affected scope**: §7 (cost-per-1k), §1
- **Finding**: "Cost-per-1k-calls" for the 4B on a 1660 needs a cost model
  (electricity at $/kWh? GPU-hour amortization? $0?). The "fraction of the
  cloud cost" headline depends on it, and two honest cost models give very
  different fractions. Unspecified.
- **Guidance**: Pick one model, state it in §7, and show the arithmetic in
  the README.

### F14. Minor gaps (Nits)
- **Severity**: Nit
- **Affected scope**: various
- **Finding**:
  - §2 step 2 lists "(C&L)" in the lookup while §4 defers C&L — make the code
    scope match (SVHC/XIV/XVII only) so the deferral is real, not half-built.
  - Model returns an EC/CAS not present in `reach.db` → lookup miss behavior
    unspecified (presumably `needs_review`; write it down).
  - §7 "disagreement log" — file format and location unspecified.
  - Demo BOM (§4) says "1 ambiguous name" — name it (or the rule for picking
    it) so the needs_review demo is deterministic.
  - Build order step 6 ("Task B only if Task A eval is clean") — "clean" is
    undefined; tie it to the F1 bar.

---

## Unstated assumptions (must become stated)

1. llama-server is already running at `127.0.0.1:8080` with the right model
   loaded; nothing in the repo starts it (§2, §12 above).
2. The 1660 can hold Q8_0 + 8K ctx (§5) — assumed, not measured.
3. `data/reach.db` has the columns/joins the pipeline needs (§7 above).
4. The cloud LLM's JSON output is reliable enough to be a label source without
   a stated validation pass beyond EC/CAS existence (§3).
5. One adapter serves both tasks via prompt alone, with no interference
   beyond the §6.4 escape hatch (§5).
6. The eval's cloud-LLM column is deterministic enough to compare (temperature
   / sampling for the cloud model unstated).

## Contradictions

1. §3 Task B: model labels are "not a runtime branch," yet §2 step 4 is a
   runtime model call whose output's destination is unspecified (F10).
2. §3 drops unresolvable training examples, while §6.2 declares abstention the
   designed behavior (F6).
3. §1 claims the deterministic parts are "exact," while §2 step 3's rules
   contain an unstated unit conflation (product volume vs. substance
   tonnage) and undefined boundaries (F8).
4. Brief Q1 and Q5 are flagged "for Goldfish attack"; the design carries both
   forward unresolved while marking itself the build specification.

## Weakest points (ranked)

1. **The eval design (F1, F2, F5)** — the number the whole POC sells is the
   least controlled: no bar, no named comparator, no leakage rule.
2. **The fine-tune task spec (F3, F4, F6)** — you cannot generate training
   data from this document; the implementer would be designing the product.
3. **The "deterministic = exact" claim (F7, F8, F11)** — the credibility
   anchor has no schema, no complete rule table, and no tests.

## What is ready

§9 step 1 (deterministic core on the demo BOM with a stub resolver) can start
immediately, provided F7/F8/F9 are closed first — the schema, rule table, and
CLI/CSV contracts are its direct inputs.

## Verdict

**NEEDS-WORK.** Blockers: F1 (eval bar), F2 (named cloud model), F3 (task
prompt/response spec). Majors F4–F13 should be closed before fine-tuning
begins (build order step 2); the deterministic core may proceed in parallel
once F7–F9 land. Re-review after revision.
