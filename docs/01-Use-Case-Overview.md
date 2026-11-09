# REACH Compliance Copilot — Use Case Overview

## One-Sentence Pitch

> **Turn a days-long, error-prone manual regulatory cross-check into a seconds-long, auditable, continuously-monitored automated process — and catch new obligations before they become fines.**

## The Problem

A chemical manufacturer, importer, or downstream user must, for every substance in their products, determine:

1. Is it on the **Candidate List (SVHC)**? → triggers communication + reporting duties
2. Is it on **Annex XIV**? → needs authorisation before use
3. Is it on **Annex XVII**? → restricted/banned above thresholds
4. What **CLP classification/labeling** is required?
5. What are the **volume-based registration** thresholds (1t/10t/100t)?

Today this is done by a regulatory specialist manually cross-referencing PDFs and spreadsheets. It's slow, error-prone, and the lists change (new SVHCs added ~twice a year).

## The Solution

An agentic AI system that:

- **Ingests** a product's composition (BOM, SDS, or a simple CSV of substances + percentages)
- **Resolves** each substance to canonical IDs (name → EC/CAS via PubChem, handling synonyms)
- **Cross-checks** against all four ECHA lists + C&L inventory
- **Reasons** about thresholds (e.g., "this SVHC is at 0.8% in the article, below the 0.1% reporting threshold → no action, but flag for monitoring")
- **Outputs** a compliance report: obligations, gaps, deadlines, and a risk score — with citations to the exact ECHA list entry

## Why It's a Great Showcase

| Property | Why it matters |
|---|---|
| **Verifiable correctness** | Ground truth exists (the actual ECHA lists) — you can prove the agent is right, not just "sounds plausible" |
| **Multi-step tool use** | ID resolution, list lookup, threshold math, report generation = a real agent loop, not a single prompt |
| **Live data** | Demo "a new SVHC was added last month, here's what it means for your portfolio" |
| **Clear business impact** | Non-compliance with REACH carries fines up to €1.5M or 4% of turnover |

## Target Users

- Chemical manufacturers (EU + non-EU exporting to EU)
- Importers of articles into the EU
- Downstream users (formulators, manufacturers of finished goods)
- Regulatory affairs / compliance teams
- Procurement teams (supplier compliance verification)

## Key Metrics (for stakeholder pitch)

- **Time to compliance check:** days → seconds
- **Error rate:** manual cross-referencing errors → near-zero (verifiable against ground truth)
- **Coverage:** full portfolio re-check on every ECHA list update (currently done ad-hoc or not at all)
- **Risk reduction:** proactive gap identification before audit, not after
