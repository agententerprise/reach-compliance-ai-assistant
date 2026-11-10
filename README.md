# REACH Compliance Copilot

> Turn a days-long, error-prone manual regulatory cross-check into a seconds-long, auditable process — and catch new REACH obligations before they become fines. **100% local: two GPUs, no cloud.**

## The claim

> The 4B resolves substance names. Python computes the obligations. The eval proves the resolution number. Everything runs on two local GPUs — no cloud.

A fine-tuned **Qwen3 4B** on a 6GB card resolves substance names to canonical
EC/CAS IDs at accuracy within a stated margin of the local 27B, at lower
latency and power. Deterministic Python does everything that must be exact.

## The system (hybrid by design)

| Layer | Does | Why |
|---|---|---|
| **Fine-tuned Qwen3 4B** (GGUF Q8_0, llama-server on RTX 1660, 6GB) | substance name → EC/CAS, with confidence + abstention | narrow, high-volume, verifiable task |
| **Deterministic Python** | SQLite list lookup (SVHC / Annex XIV / Annex XVII), threshold rules (0.1% SVHC, authorisation, restriction flag), report assembly with citations | exact, auditable, unit-tested, no LLM in the loop |
| **Qwen 27B** (llama-server on RTX 3090, 24GB) | teacher (training labels) + judge (eval reference) — lab only, never in the demo path | local big model; no cloud anywhere |

Out of POC scope (stated in reports): registration tiers, C&L inventory,
Annex XVII condition evaluation (flag + quote), model-based obligation labels.

## Eval (the number the repo exists to produce)

- 200-name **human-verified** held-out set; both models scored against it
- bar: 4B ≥90% exact EC-match, within 5 points of the 27B, 95% CIs reported
- table: accuracy / latency-per-1k / power-per-1k (4B-1660 vs 27B-3090)

## Repo layout

```
src/reach/          pipeline package (resolve, check, obligations, report, cli)
data/               ECHA lists (SVHC, Annex XIV, Annex XVII) + reach.db + VERSIONS.md
docs/               use-case docs + EGM design spec + Goldfish review reports
eval/               eval harness + held-out sets
finetune/           data generation, LoRA script (3090), GGUF export (Q8_0)
demos/              demo BOM + sample report
tests/              rule unit tests + golden report test
```

## Quick start

```bash
python3 -m reach check demos/bom_demo.csv --db data/reach.db \
  --resolver stub --out report.md        # deterministic core, no GPU needed
```

The fine-tuned GGUF ships as a GitHub release asset; the GPU path points
`--model` at your local llama-server.

## Status

- ✅ ECHA data layer (CSVs → SQLite)
- ✅ EGM design spec v2 (post-Goldfish review) — `docs/designs/`
- ⏳ deterministic core + tests → fine-tune → eval table → demo
