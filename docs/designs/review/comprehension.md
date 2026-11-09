# Goldfish Review — Comprehension (Naive Reader)

*Target: `docs/designs/reach-compliance-copilot.md` (DRAFT) + `concepts_brief.md`
Reviewer: Comprehension Goldfish (EGM). Zero prior context. Read-only audit.*

I read both documents as a fresh team member with no REACH, no LLM fine-tuning,
and no prior session history. Findings below are ordered by severity.

---

## Blockers

### B1. The success criterion is unmeasurable: "within a small, stated margin"
- **Scope:** §1 (Purpose and success criteria)
- The entire POC exists to produce one honest number, but the margin is never
  stated. §1 says "accuracy within a small, stated margin of a cloud big LLM"
  — the margin is not stated anywhere in the design. The brief's open question
  5 ("within X points" vs "statistically indistinguishable", on what task set)
  is listed as *for Goldfish attack* and the design never resolves it. A reader
  cannot tell what "success" means operationally. Also: "cloud big LLM" is
  never named — which model, which API, which price list? Cost-per-1k is
  meaningless without a named reference model.
- **Fix required:** name the teacher/judge model, state the numeric accuracy
  bar and the task set it applies to, before build order step 5.

### B2. Label validation checks existence, not correctness
- **Scope:** §3, Task A ("training labels")
- "The emitted EC/CAS must exist in the ECHA data or PubChem; invalid labels
  dropped." A label can exist in ECHA and still be the *wrong substance* for
  the input name (e.g., the LLM confuses two real chemicals with distinct EC
  numbers). The stated validation accepts every such error. Since the whole
  claim is "4B ≈ big LLM accuracy," the training labels are the ceiling, and
  the doc gives no indication of how often teacher labels are actually correct
  (no human spot-check rate, no double-teacher agreement, no stated label
  accuracy). A naive reader concludes the accuracy number in §7 may be bounded
  by unmeasured label noise, and the doc never addresses that.
- **Fix required:** state a label-quality procedure (e.g., N% human spot-check,
  cross-teacher agreement) and report the resulting label accuracy.

### B3. No glossary; ~15 domain terms are used without definition or link
- **Scope:** whole document
- Undefined for a fresh reader: REACH, ECHA, SVHC, Candidate List, Annex XIV,
  Annex XVII, C&L (classification & labelling), EC number, CAS number, BOM,
  SDS, article (vs substance), PUG-REST, GGUF, Q8_0/Q6_K, LoRA, Unsloth,
  llama-server, "teacher model". The brief uses them too. None is defined
  inline, in a glossary, or linked. The doc is a *build specification* that
  will be read by people who are not chemists and not LLM engineers; as
  written it assumes both.
- **Fix required:** a short glossary section (or inline definitions on first
  use) covering at minimum: REACH, ECHA, SVHC, Annex XIV/XVII, C&L, EC/CAS,
  BOM, article, GGUF, LoRA.

---

## Major

### M1. Brief and design contradict each other on the cloud LLM's runtime role
- **Scope:** brief "Division of labor" table vs design §2/§4
- The brief's table says the cloud big LLM is the "fallback for
  low-confidence resolutions" — a *runtime* role — while the same table's
  "Does NOT do" column says "nothing at runtime in the demo path." The design
  resolves this (low confidence → `needs_review`, no runtime cloud call),
  which is the right call, but the brief — the document a reader is told to
  read alongside — still carries the contradiction. Whichever doc is read
  first, the reader hits a conflict.
- **Fix required:** update the brief's table to match design §2.

### M2. Task B's purpose is circular and its runtime role is vague
- **Scope:** §3 Task B; §2 step [4]; §9 step 6
- Task B exists to "(a) produce the plain-language summary line and (b) be the
  thing we fine-tune and eval." (b) is circular: we fine-tune the classifier
  so that we can evaluate the classifier. If the deterministic rules are "the
  source of truth" and "the report cites them, not the model," then the
  model's obligation *labels* do nothing at runtime — only the summary line
  does. So why eval obligation labels at all (≥100 items in §7)? The doc
  never says what the eval of Task B is *for* if its output is discarded.
  Also step [4] is marked "(optional)" in §2 but Task B has a firm slot in
  the build order (§9 step 6) and a firm eval budget (§7). "Optional" and
  "planned with 100 eval items" are in tension.
- **Fix required:** state explicitly: Task B labels are eval-only; the runtime
  artifact is the summary line; and what a bad Task B eval number would change
  (presumably: drop the summary line, ship resolution-only — as §6.4 implies
  but doesn't say for the summary line).

### M3. "Confidence" is emitted by the model but never defined
- **Scope:** §2 step [1]; §3 Task A; §7
- The model outputs `confidence: high|medium|low`, and low confidence routes
  to `needs_review`. But: how does the model decide? (Presumably learned from
  teacher labels — but the teacher's confidence policy is never specified, so
  the training data's confidence distribution is undefined.) §7 mentions
  "abstention calibration" as an output, but no metric is defined (what is
  calibration here? coverage? abstention rate on a labeled-ambiguous set?).
  The demo BOM contains exactly 1 ambiguous name — one data point cannot
  demonstrate calibration.
- **Fix required:** define the teacher's abstention rule, the calibration
  metric, and accept that calibration is illustrative, not measured, at POC
  scale.

### M4. The REACH rules in §2 step [3] are simplifications the doc doesn't flag
- **Scope:** §2 step [3]; §3 Task B
- Three issues a naive (or domain) reader will catch:
  1. "SVHC: conc > 0.1% in article → communication duty" — this duty applies
     to *articles* (and mixtures); the doc never states the demo BOM is
     assumed to describe an article. The BOM has a "use context" column, but
     the rule ignores it.
  2. "registration tiers: 1t / 10t / 100t by volume" — in REACH, registration
     is triggered at 1 t/yr per substance per manufacturer; 10 t/100 t change
     the *dossier content*, not the obligation. Presenting "registration_tier_10t"
     as an obligation label (§3 Task B) is a category error. Also: whose
     volume? A product BOM's "annual volume t" is presumably the *article*
     maker's volume, but registration attaches to the *substance* maker. The
     doc never says whose volume the BOM column represents.
  3. "Annex XIV: any use → authorisation required" — true for the substance
     in the article, but the nuance (grandfathering, exemptions) is silently
     dropped without a §6-style caveat.
- These are POC-scope simplifications, which is fine — but §6 "Known weak
  points" lists only Annex XVII conditions. The other two simplifications
  should be listed there too, because the Substack post will quote these rules.

### M5. Held-out eval sets: provenance and contamination unstated
- **Scope:** §7
- "Runs a held-out set (≥200 resolution items, ≥100 obligation items)."
  Where do these come from? Presumably generated the same way as training
  data, but the doc never says. No statement that held-out items are excluded
  from training (dedup is mentioned for training data in §5, not for the
  train/eval split). With a 4B model memorizing 2–5K generated examples,
  train/eval leakage is the classic failure mode, and the doc is silent.
  Also §6.3 says the obligation accuracy is "a curated-set number" — but §7
  calls the set "held-out," not curated. Two different characterizations of
  the same set.
- **Fix required:** state generation source, the dedup/split procedure, and
  use one consistent characterization (curated vs held-out).

### M6. "Cost-per-1k" for the local model is undefined
- **Scope:** §1, §7
- Cloud cost is a price list. Local cost on a 1660 is what — electricity?
  GPU depreciation? Amortized purchase price over an assumed lifetime? The
  three-number table is the headline deliverable ("goes in the README, the
  Substack post, and the video"), and one of its three columns has no defined
  methodology. A reader cannot reproduce or trust the number.
- **Fix required:** define the local-cost formula (e.g., $/kWh × measured
  draw × time-per-1k-calls, plus stated depreciation assumption).

### M7. Reproducibility claim vs model weights
- **Scope:** §1 ("reproducible from a clean clone"), §5, §8
- The GGUF is ~4.3 GB. The repo layout (§8) has no place for it, and no
  statement of how it's distributed (Hugging Face? git-lfs? retrain from
  `finetune/`?). "Reproducible from a clean clone" is ambiguous: does it mean
  *runnable* (needs the 4.3 GB artifact + a 6 GB GPU) or *retrainable*
  (needs a 24 GB 3090 + teacher API budget)? A naive reader cannot clone and
  run without knowing which.
- **Fix required:** state where the GGUF lives and what "reproducible"
  guarantees (run vs retrain), including hardware prerequisites.

### M8. ECHA data: versioning, dates, and licensing unstated
- **Scope:** §4, §2 step [5]
- The lists change over time (SVHC is amended regularly). The doc never pins
  the data vintage (which Candidate List version is in `reach.db`?), and the
  report cites "date" — which date? List publication date? Ingest date?
  Amendment date of the entry? For a compliance tool whose selling point is
  "citable," the citation's date semantics must be defined. Also: the repo is
  public; ECHA data licensing terms for redistribution are never mentioned.
- **Fix required:** pin the list versions in the repo (e.g., a `data/VERSIONS.md`),
  define the cited date field, and note the ECHA data license.

---

## Nits

### N1. Brief says "8–16K context"; design says "ctx 8K"
- Brief "Locked configuration" vs design §5. Minor, but the brief claims to
  be "locked" and the design quietly narrows it. Pick one.

### N2. "(C&L)" left in the pipeline diagram
- §2 step [2] shows "SVHC / Annex XIV / Annex XVII / (C&L)" while §4 says C&L
  is DEFERRED. The parenthetical is a leftover that will confuse readers
  about scope.

### N3. "Resolution pre-verified" vs the ambiguous demo name
- §1 non-goals say the demo BOM's "resolution [is] pre-verified"; §4 includes
  "1 ambiguous name to demonstrate the needs_review path." Pre-verified
  presumably means pre-verified *to be ambiguous* — say so, or the two
  statements read as contradictory.

### N4. `python -m reach check ...` assumes an install step
- §2 gives the CLI command, but §8 shows the package under `src/reach/`.
  `python -m reach` only works after `pip install -e .` (or a PYTHONPATH
  trick). One line in the doc would prevent a fresh reader's first failure.

### N5. "Q6_K fallback" appears only in the brief
- The brief lists a Q6_K fallback for when Q8_0 doesn't fit; the design drops
  it. If it's dead, remove it from the brief; if it's live, it belongs in §5.

### N6. No failure behavior for a dead llama-server
- §2 says steps 1/4 call the local server. What does `check` do if the server
  is down — crash, stub mode, `--offline`? The build order (§9 step 1) implies
  a stub resolver exists; make that a documented flag.

---

## Cross-check: brief's open questions vs design

| Brief question | Design resolution |
|---|---|
| 1. Confidence policy (abstain vs always answer) | Resolved: abstain → `needs_review` (§2, §3). Good. |
| 2. Annex XVII scope | Resolved: flag + quote condition text (§6.1). Good. |
| 3. C&L inventory | Resolved: deferred (§4). Good. |
| 4. PubChem at runtime? | Resolved: training-time only (§4). Good. |
| 5. What "matches the big LLM" means | **Not resolved.** This is B1. |

Four of five open questions were answered; the one that defines the POC's
success criterion was not.

---

## Weakest points (ranked)

1. **The eval bar is undefined (B1).** The POC's entire claim is comparative
   accuracy, and the comparison has no named opponent, no numeric bar, and no
   defined task-set semantics. Everything downstream (README, post, video)
   hangs on this.
2. **Label quality is unmeasured (B2).** Teacher-generated labels validated
   only for existence. The accuracy ceiling is unknown and unstated.
3. **The REACH rules are simplified in ways the doc doesn't admit (M4).**
   The post will quote them; the caveats must exist in §6.
4. **Task B is a mystery (M2).** Its runtime output is discarded, its eval
   purpose is unstated, and its "optional" status conflicts with its planned
   budget.

---

## Verdict: **NEEDS-WORK**

The architecture is sound and the build order is sensible — the deterministic
core first, model second, is the right shape, and §6's honesty about weak
points is a strength. But the document cannot currently tell a reader what
"success" means (B1), how trustworthy the training labels are (B2), or what
the domain terms mean (B3). Fix the three blockers and the M1/M4/M5/M6
majors, and this is ready to build.
