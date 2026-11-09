# Concepts Brief — REACH Compliance Copilot POC

*EGM brainstorm output. Elephant: pi session (Nov 10). Status: draft for Goldfish review.*

## What we are building (and why)

A proof-of-concept that demonstrates one specific claim:

> A fine-tuned 4B model, running on a 6GB on-prem GPU, resolves substance
> names to canonical IDs at accuracy within a stated margin of a cloud big
> LLM, at a fraction of the cost and latency. (Obligation classification by
> the model was cut from POC scope after Goldfish review — obligations are
> computed by deterministic code; see design doc v2, §3.)

The POC is a **showcase asset**, not a product. The deliverables are:

1. A public GitHub repo (`agententerprise/reach-compliance-copilot`) with a working end-to-end pipeline
2. A Substack post
3. A LinkedIn post
4. A short demo video

It is the first concrete build in the "Small Language Models for Enterprise"
portfolio (REACH, VOC, PSR, Adaptive-Invoice-Extraction, Opportunity-Discovery).
Everything it establishes — data format, fine-tune script, GGUF export, eval
harness, report format — is intended to be reused by the other four use cases.

## What the system does

Input: a product Bill of Materials (CSV: substance name, concentration %,
annual volume t, use context).

Output: a compliance report — for each substance: canonical ID (EC/CAS),
which ECHA lists it hits (SVHC Candidate List, Annex XIV, Annex XVII, C&L),
which obligations are triggered given concentration and volume, citations to
the exact list entries, and items flagged for human review.

## Division of labor (locked)

| Component | Does | Does NOT do |
|---|---|---|
| Fine-tuned Qwen3 4B (GGUF Q8_0, llama-server on 1660) | name → EC/CAS resolution (with confidence/abstention) | threshold math, list lookup, report assembly, orchestration, obligation labels |
| Deterministic Python | SQLite list lookup, threshold rules (0.1% SVHC, Annex XIV, Annex XVII flag), report assembly, validation | any language understanding |
| Cloud big LLM | generates training labels (teacher); eval reference (judge) | nothing at runtime in the demo path (low confidence → needs_review, no cloud call) |

## Locked configuration (from prior sessions)

- Base model: Qwen3 4B (text)
- Fine-tune: LoRA r=16, alpha=32, Unsloth, on RTX 3090 (24GB)
- Export: GGUF Q8_0 (~4.3GB); Q6_K fallback
- Serve: llama.cpp `llama-server` on RTX 1660 (6GB), 8K context (16K does not fit in 6GB), thinking mode off
- Training data: JSONL instruction format; cloud big LLM as teacher; labels
  validated against the ECHA lists
- Eval: fine-tuned 4B (1660) vs cloud big LLM → accuracy / cost-per-1k /
  latency-per-1k table
- Showcase principle: bounded input structure (BOM/SDS) → clean, reliable
  accuracy number

## Current state

- Done: ECHA CSVs downloaded (SVHC, Annex XIV, Annex XVII), ingested to
  SQLite (`data/reach.db`), ingest scripts in `src/`
- Not done: C&L inventory ingestion (~7M rows — size decision needed),
  resolver, checker, report pipeline, demo BOM, fine-tune data, model,
  eval harness

## Open questions (for Goldfish attack)

All five resolved in design v2 (docs/designs/reach-compliance-copilot.md):
1. Confidence: low → needs_review; abstention is a trained, evaluated feature
2. Annex XVII: flag + quote condition text; human decides
3. C&L: deferred (POC = SVHC + XIV + XVII)
4. PubChem: training-time only
5. Eval bar: ≥90% exact-match, within 5pts of named cloud model, n=200,
   CIs reported — pending user sign-off (design §10)
