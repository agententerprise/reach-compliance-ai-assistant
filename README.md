# REACH Compliance - AI Assistant

Check your product compositions against EU REACH regulatory lists in seconds — with citations.

Given a product Bill of Materials (substances, concentrations, volumes), the assistant tells you:

- which substances are on the **SVHC Candidate List** and whether the 0.1% article threshold is exceeded
- which require **authorisation** (Annex XIV)
- which are **restricted** (Annex XVII) — with the restriction condition quoted
- which items need **human review** (the assistant abstains rather than guess)

Every finding carries a citation to the exact ECHA list entry. The assistant runs fully on-prem — your composition data never leaves your machine.

## The model

The assistant is built on a fine-tuned [Qwen3 4B](https://huggingface.co) for chemical substance identification, quantized to run on a 6GB GPU.

- Model: `[Hugging Face — coming soon]`
- Runtime: [llama.cpp](https://github.com/ggml-org/llama.cpp) `llama-server`, 8K context

## Install

```bash
git clone https://github.com/agententerprise/reach-compliance-ai-assistant
cd reach-compliance-ai-assistant
pip install -e .
```

The ECHA regulatory lists (SVHC, Annex XIV, Annex XVII) are included as a
local SQLite database — no download step, no API keys.

## Usage

```bash
# with the local model
python -m reach check bom.csv --db data/reach.db \
  --model http://127.0.0.1:8080 --out report.md

# without a GPU (deterministic core only, IDs supplied)
python -m reach check bom.csv --db data/reach.db \
  --resolver stub --ids bom_ids.csv --out report.md
```

Input CSV format:

```csv
name,conc_pct,volume_t,use
Titanium Dioxide,12.0,500,article
```

`use` is one of `article`, `mixture`, `substance`. Output is a Markdown
report (and `--json` for machine-readable results) with per-substance
findings, obligations, citations, and a needs-review section.

## Example

See `demos/` for a sample BOM and the report it produces.

## Scope

This release covers SVHC communication duties, Annex XIV authorisation, and
Annex XVII restriction flags. Not included: registration tonnage tiers,
C&L classification/labeling, and evaluation of Annex XVII use-specific
conditions (restricted entries are flagged with the condition text quoted
for your review).

## Data

ECHA open data, versions pinned in `data/VERSIONS.md`.

## License

[TODO]
