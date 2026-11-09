# Problems Solved

## 1. Manual cross-referencing is slow and error-prone

**Problem:** A regulatory specialist takes a product composition and manually checks each substance against 4+ ECHA lists (SVHC, Annex XIV, Annex XVII, C&L). For a portfolio of hundreds of products, this is days of spreadsheet work.

**Solved:** Agent does it in seconds, consistently, no copy-paste errors.

## 2. The lists change constantly

**Problem:** ECHA adds new SVHCs ~twice a year, updates restrictions, adds authorisation entries. Companies must re-check their entire portfolio every time. Most don't — they find out about a new obligation only when a customer or auditor asks.

**Solved:** Re-run the agent on the updated lists → instant "here's what changed for you" report. This is the killer feature — **continuous compliance monitoring**, not a one-time check.

## 3. Substance ID resolution is genuinely hard

**Problem:** The same chemical has dozens of names (CAS, EC, INCI, trade names, synonyms). A BOM might say "Titanium Dioxide" while the ECHA list says "Titanium dioxide (EC 231-791-2)". Manual matching is where mistakes happen.

**Solved:** Agent uses PubChem to resolve names → canonical IDs, handling synonyms automatically. This is a real agentic capability, not just a lookup.

## 4. Threshold reasoning requires domain expertise

**Problem:** Being on the SVHC list doesn't automatically mean you have an obligation. It depends on concentration (0.1% threshold for articles), volume (1t/10t/100t registration tiers), and use case. Getting this wrong means either over-complying (wasted cost) or under-complying (fines).

**Solved:** Agent reasons about the actual numbers in your BOM and tells you precisely what's triggered and what isn't, with the regulatory citation.

## 5. Non-compliance is expensive

**Problem:** REACH violations carry fines up to **€1.5M or 4% of annual turnover**. Missed SVHC communication, unauthorised use of Annex XIV substances, or restricted substances above limits are all real legal risks. Even without fines, there's supply chain risk — customers demand REACH compliance declarations.

**Solved:** Proactive gap identification before you're in violation, not after an audit.

## 6. Knowledge is siloed

**Problem:** The person who knows REACH well is often one person. When they leave, the knowledge goes. New products get checked inconsistently.

**Solved:** The agent encodes the regulatory logic. It's consistent, auditable, and doesn't leave the building.

## 7. Customer/supply chain pressure

**Problem:** Downstream customers (especially in EU) increasingly demand REACH compliance declarations before doing business. "Is your product SVHC-free?" is a standard procurement question.

**Solved:** Generate a compliance declaration per product in seconds, with citations.

## Demo Script (2 min)

1. Upload a sample product BOM (5–10 substances, one of which is a recent SVHC)
2. Watch the agent resolve IDs, hit each list, and reason about thresholds
3. It flags: "Substance X (EC 2xx-xxx) is on the Candidate List as of [date] at 1.2% in your article → **communication to ECHA required within 3 months**"
4. Show the cited report

## Most Impactful Demo Angle

**Continuous monitoring** — show that a new SVHC was added last month, and the agent immediately flags which products in the portfolio are affected. That's the "oh wow" moment that a static spreadsheet can't do.
