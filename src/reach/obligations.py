"""Deterministic obligation rules.

These are the source of truth for what a hit means. No model is involved:
given list hits and a concentration, the obligations follow by rule.

Scope notes (locked design decisions):
- Registration tiers are NOT derived here: REACH tonnage is aggregated
  per-substance per-manufacturer across all articles, so a single BOM
  row cannot establish a tier.
- Annex XVII conditions are entry-specific; we flag for review rather
  than interpret each of the ~1900 entries.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .check import ListHits

SVHC_COMMUNICATION_THRESHOLD_PCT = 0.1  # Art. 33(2): 0.1% w/w


@dataclass(frozen=True)
class Obligation:
    code: str            # machine-readable, e.g. "SVHC_ART33"
    title: str
    detail: str
    citation: str        # list + entry + date, for the report


@dataclass(frozen=True)
class ArticleFinding:
    substance: str
    ec_no: str | None
    cas_no: str | None
    concentration_pct: float | None
    obligations: list[Obligation] = field(default_factory=list)
    needs_review: bool = False
    review_reason: str | None = None

    @property
    def clean(self) -> bool:
        return not self.obligations and not self.needs_review


def derive_obligations(hits: ListHits, concentration_pct: float | None) -> list[Obligation]:
    """Apply the deterministic rules to one substance's list hits."""
    out: list[Obligation] = []

    if hits.svhc is not None:
        s = hits.svhc
        cite = (
            f"SVHC Candidate List, {s['ec_no']} ({s['name']}), "
            f"included {s['date_inclusion'] or 'date n/a'}"
        )
        if concentration_pct is not None and concentration_pct >= SVHC_COMMUNICATION_THRESHOLD_PCT:
            out.append(
                Obligation(
                    code="SVHC_ART33",
                    title="Article 33 communication obligation",
                    detail=(
                        f"SVHC at {concentration_pct:.2f}% w/w meets or exceeds the "
                        f"{SVHC_COMMUNICATION_THRESHOLD_PCT}% threshold: information "
                        f"must be provided to downstream users and (on request) to "
                        f"consumers. Stated reason: {s['reason'] or 'n/a'}."
                    ),
                    citation=cite,
                )
            )
        elif concentration_pct is not None:
            out.append(
                Obligation(
                    code="SVHC_BELOW_THRESHOLD",
                    title="SVHC below 0.1% — no Art. 33 duty",
                    detail=(
                        f"SVHC at {concentration_pct:.2f}% w/w is below the "
                        f"{SVHC_COMMUNICATION_THRESHOLD_PCT}% communication threshold. "
                        f"Track for formulation changes that could raise its share."
                    ),
                    citation=cite,
                )
            )
        else:
            out.append(
                Obligation(
                    code="SVHC_CONCENTRATION_UNKNOWN",
                    title="SVHC — concentration unknown",
                    detail=(
                        "Listed SVHC but the BOM carries no concentration; the "
                        "0.1% Art. 33 test cannot be applied. Obtain the weight "
                        "percentage before concluding."
                    ),
                    citation=cite,
                )
            )

    if hits.annex14 is not None:
        a = hits.annex14
        out.append(
            Obligation(
                code="ANNEX14_AUTHORISATION",
                title="Annex XIV — authorisation required",
                detail=(
                    f"Entry {a['entry_no'] or 'n/a'}: use of this substance in "
                    f"articles requires an authorisation or a valid exemption. "
                    f"Conditions: {(a['conditions'] or 'see entry')[:300]}"
                ),
                citation=(
                    f"Annex XIV, entry {a['entry_no'] or 'n/a'}, "
                    f"{a['ec_no']} ({a['name']}), included {a['date_inclusion'] or 'date n/a'}"
                ),
            )
        )

    for r in hits.annex17 or []:
        out.append(
            Obligation(
                code="ANNEX17_RESTRICTION",
                title=f"Annex XVII — restriction (entry {r['entry_no'] or 'n/a'})",
                detail=(
                    "Restricted substance: the entry's conditions limit its "
                    "placement on the market or use in articles. Review the entry "
                    "text for applicability to this article."
                ),
                citation=(
                    f"Annex XVII, entry {r['entry_no'] or 'n/a'}, "
                    f"{r['ec_no']} ({r['name']}), "
                    f"first published {r['first_published'] or 'date n/a'}"
                ),
            )
        )

    return out
