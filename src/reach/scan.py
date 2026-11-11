"""End-to-end scan: BOM rows -> findings.

Wires resolver -> check -> obligations. The resolver is injected so the
same pipeline runs with the stub today and the fine-tuned 4B tomorrow.
"""

from __future__ import annotations

import csv
import sqlite3
from dataclasses import dataclass

from .check import check_substance
from .obligations import ArticleFinding, derive_obligations
from .resolver import Confidence, Resolver


@dataclass(frozen=True)
class BomRow:
    article: str
    substance: str
    concentration_pct: float | None


def parse_bom(path: str) -> list[BomRow]:
    """Read a BOM CSV.

    Expected columns: article, substance, concentration_pct
    (concentration_pct optional; blank = unknown).
    """
    rows: list[BomRow] = []
    with open(path, newline="", encoding="utf-8") as f:
        for i, rec in enumerate(csv.DictReader(f), start=2):
            sub = (rec.get("substance") or "").strip()
            if not sub:
                continue
            conc_raw = (rec.get("concentration_pct") or "").strip()
            try:
                conc = float(conc_raw) if conc_raw else None
            except ValueError:
                conc = None
            rows.append(
                BomRow(
                    article=(rec.get("article") or f"row-{i}").strip(),
                    substance=sub,
                    concentration_pct=conc,
                )
            )
    return rows


def scan_row(conn: sqlite3.Connection, resolver: Resolver, row: BomRow) -> ArticleFinding:
    """Resolve one BOM row and derive its obligations."""
    res = resolver.resolve(row.substance)

    if not res.resolved:
        return ArticleFinding(
            substance=row.substance,
            ec_no=res.ec_no,
            cas_no=res.cas_no,
            concentration_pct=row.concentration_pct,
            needs_review=True,
            review_reason=(
                "name could not be resolved to an EC/CAS identity "
                f"(confidence: {res.confidence.value})"
            ),
        )

    hits = check_substance(conn, res.ec_no, res.cas_no)
    obligations = derive_obligations(hits, row.concentration_pct)

    needs_review = res.confidence == Confidence.MEDIUM
    reason = (
        "resolution confidence is medium — verify the matched identity"
        if needs_review
        else None
    )
    if res.matched_name and res.matched_name.casefold() != row.substance.casefold():
        reason = (
            f"matched to '{res.matched_name}' — confirm this is the intended substance"
            if not needs_review
            else reason
        )
        needs_review = needs_review or bool(
            res.matched_name and res.matched_name.casefold() != row.substance.casefold()
        )

    return ArticleFinding(
        substance=row.substance,
        ec_no=res.ec_no,
        cas_no=res.cas_no,
        concentration_pct=row.concentration_pct,
        obligations=obligations,
        needs_review=needs_review,
        review_reason=reason,
    )


def scan_bom(conn: sqlite3.Connection, resolver: Resolver, rows: list[BomRow]) -> list[ArticleFinding]:
    return [scan_row(conn, resolver, r) for r in rows]
