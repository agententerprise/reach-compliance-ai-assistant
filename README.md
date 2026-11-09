# REACH Compliance Copilot

> Turn a days-long, error-prone manual regulatory cross-check into a seconds-long, auditable, continuously-monitored automated process — and catch new obligations before they become fines.

## The system (hybrid by design)

| Layer | Does | Why |
|---|---|---|
| **Fine-tuned Qwen3 4B** (LoRA on 3090 → GGUF Q8_0 on 1660, on-prem) | substance name → canonical ID (EC/CAS); (substance, conc, volume, use) → obligation label | narrow, high-volume, verifiable tasks |
| **Deterministic Python** | list lookup, threshold math (0.1%/1t/10t/100t), report assembly against ECHA lists in SQLite | exact, auditable, no LLM in the loop |
| **Big LLM** | teacher (training labels), judge (eval reference), fallback | safety net |

## Repo layout

```
src/        ingest.py (CSV→SQLite), fetch_echa.py, debug_echa.py
data/       ECHA lists (SVHC Candidate List, Annex XIV, Annex XVII) + reach.db
docs/       use-case docs (overview, problems solved, data sources & architecture)
eval/       SLM vs big-LLM harness (accuracy / cost-per-1k / latency-per-1k)   [coming]
finetune/   LoRA script (3090) + GGUF export (Q8_0)                            [coming]
```

## Quick start

```bash
python3 src/ingest.py data data/reach.db   # rebuild SQLite from the ECHA CSVs
```

## Status

POC in progress — data layer done (ECHA lists ingested to SQLite); SLM fine-tune, eval harness, and demo BOM next.
