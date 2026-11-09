# Data Sources & Architecture

## Data Sources

| Source | What it gives you | Access |
|---|---|---|
| **ECHA Candidate List (SVHC)** | ~247+ Substances of Very High Concern, with EC/CAS numbers, reasons for concern, dates | CSV download via data.europa.eu (open data, free) |
| **ECHA C&L Inventory** | ~7M classification entries, ~350k substances, harmonised EU hazard classes | CSV/XML via data.europa.eu; new ECHA CHEM API coming |
| **ECHA Annex XIV (Authorisation)** | Substances needing authorisation before use | CSV via data.europa.eu |
| **ECHA Annex XVII (Restrictions)** | Substances restricted/banned above thresholds | CSV via data.europa.eu |
| **PubChem PUG-REST** | Structure, properties, synonyms, GHS, toxicity for millions of compounds | Free REST API, no key |
| **ECHA CHEM** | Unified new database (launched 2025) | Web + API "soon" |

### Key Insight

**The raw regulatory data is free and open.** The value isn't in the data — it's in the *reasoning* that connects a company's product composition to obligations. That's exactly where an agent shines.

### Data URLs

- Candidate List: https://data.europa.eu/data/datasets/candidate-list-of-substances-of-very-high-concern-for-authorisation
- C&L Inventory: https://data.europa.eu/data/datasets/echa-classification-and-labelling-inventory
- Authorisation List: https://data.europa.eu/data/datasets/authorisation-list
- PubChem PUG-REST: https://pubchem.ncbi.nlm.nih.gov/rest/pug/
- ECHA CHEM: https://chem.echa.europa.eu/

## Architecture

```
[Product BOM / SDS input]
        │
   ┌────▼─────────────────────────┐
   │  Orchestrator Agent          │
   │  (plans the compliance check)│
   └────┬─────────────────────────┘
        │
   ┌────▼─────┐  ┌──────────┐  ┌──────────────┐
   │ Resolver │  │ List     │  │ Threshold    │
   │ Agent    │  │ Checker  │  │ Reasoner     │
   │ name→ID  │  │ SVHC/XIV │  │ volume & %   │
   │ via      │  │ XVII/C&L │  │ math         │
   │ PubChem  │  │ (local   │  │              │
   │          │  │  CSVs)   │  │              │
   └────┬─────┘  └────┬─────┘  └──────┬───────┘
        └──────────────┼───────────────┘
                   ┌───▼────┐
                   │ Report │  obligations, gaps,
                   │ Agent  │  risk score, citations
                   └────────┘
```

### Data Layer

- Pre-download the ECHA CSVs (SVHC, Annex XIV, Annex XVII, C&L) into a local **SQLite/Postgres**
- Use **PubChem PUG-REST** live for ID resolution
- Keeps the agent fast and the regulatory data authoritative

### Agent Roles

| Agent | Responsibility | Tools |
|---|---|---|
| **Orchestrator** | Plans the compliance check, coordinates sub-agents, handles edge cases | Task planning, sub-agent dispatch |
| **Resolver** | Resolves substance names → canonical IDs (EC/CAS) | PubChem PUG-REST API, synonym matching |
| **List Checker** | Cross-checks resolved IDs against all ECHA lists | Local DB queries (SQLite/Postgres) |
| **Threshold Reasoner** | Applies concentration/volume thresholds, determines actual obligations | Regulatory rules engine + LLM reasoning |
| **Report Agent** | Generates the final compliance report with citations | Report template, citation lookup |

## Tech Stack (suggested)

- **Language:** Python
- **Agent framework:** LangGraph / CrewAI / custom loop
- **LLM:** GPT-4 / Claude / local (for ID resolution + reasoning)
- **Database:** SQLite (dev) → Postgres (prod)
- **Data ingestion:** Python scripts to download + parse ECHA CSVs
- **API:** FastAPI (if exposing as a service)
- **Frontend:** Simple web UI or CLI for demo

## Build Phases

### Phase 1: Data Foundation (Week 1)
- [ ] Download ECHA CSVs (SVHC, Annex XIV, Annex XVII, C&L)
- [ ] Parse into SQLite schema
- [ ] Build PubChem ID resolution function
- [ ] Test with 10 known substances

### Phase 2: Core Agent Loop (Week 2)
- [ ] Implement Orchestrator + Resolver + List Checker
- [ ] Input: CSV BOM (substance name, concentration %, annual volume)
- [ ] Output: JSON compliance results
- [ ] Test with sample BOM containing known SVHC

### Phase 3: Threshold Reasoning (Week 3)
- [ ] Encode REACH threshold rules (0.1% SVHC, 1t/10t/100t tiers)
- [ ] Threshold Reasoner agent
- [ ] Edge cases: mixtures, articles, consumer vs industrial use

### Phase 4: Report Generation (Week 4)
- [ ] Report Agent with citations
- [ ] Risk scoring
- [ ] PDF/HTML output
- [ ] Demo BOM with recent SVHC addition

### Phase 5: Continuous Monitoring (Week 5)
- [ ] Scheduled ECHA list refresh
- [ ] Diff detection (new/changed entries)
- [ ] "What changed for you" alert report
- [ ] Dashboard (optional)
