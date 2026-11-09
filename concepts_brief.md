# Concepts Brief — REACH Compliance Copilot POC

*EGM brainstorm output. Elephant: pi session (Nov 10). Status: draft for Goldfish review.*

## What we are building (and why)

A proof-of-concept that demonstrates one specific claim:

> A fine-tuned 4B model, running on a 6GB on-prem GPU, handles the narrow
> language tasks of REACH chemical compliance (substance name → canonical ID,
> obligation classification) at accuracy close to a cloud big LLM, at a
> fraction of the cost and latency.

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
| Fine-tuned Qwen3 4B (GGUF Q8_0, llama-server on 1660) | name → EC/CAS resolution; (substance, conc, volume, use) → obligation label | threshold math, list lookup, report assembly, orchestration |
| Deterministic Python | SQLite list lookup, threshold math (0.1% SVHC, 1t/10t/100t tiers), report assembly, validation | any language understanding |
| Cloud big LLM | generates training labels (teacher); eval reference (judge); fallback for low-confidence resolutions | nothing at runtime in the demo path |

## Locked configuration (from prior sessions)

- Base model: Qwen3 4B (text)
- Fine-tune: LoRA r=16, alpha=32, Unsloth, on RTX 3090 (24GB)
- Export: GGUF Q8_0 (~4.3GB); Q6_K fallback
- Serve: llama.cpp `llama-server` on RTX 1660 (6GB), 8–16K context
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

1. **Confidence policy**: when name→ID is ambiguous, does the system abstain
   ("needs review") or always answer? Working assumption: abstention is a
   feature — a compliance tool that flags low-confidence resolutions is more
   credible than one that always cites.
2. **Annex XVII scope**: restrictions are per-entry with complex conditions
   (use-specific limits, not just concentration). Can a 4B obligation
   classifier handle Annex XVII entries honestly, or does Annex XVII stay
   "flag for human review" in the POC?
3. **C&L inventory**: 7M rows. Include in POC (full classification/labeling
   answers) or defer (POC covers SVHC + XIV + XVII only)?
4. **PubChem at runtime**: the docs say PubChem PUG-REST for resolution. But
   the fine-tuned 4B is *supposed* to do name→ID. Is PubChem a training-time
   label source, a runtime fallback, or both?
5. **What "matches the big LLM" means in eval**: on what task set, what
   accuracy bar, and is the bar "within X points" or "statistically
   indistinguishable"?
