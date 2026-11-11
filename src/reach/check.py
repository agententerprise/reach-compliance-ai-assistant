"""List lookup: which ECHA lists contain a resolved substance?"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class ListHits:
    ec_no: str
    cas_no: str | None
    svhc: dict | None = None        # svhc_entries row
    annex14: dict | None = None     # annex14_entries row
    annex17: list[dict] | None = None  # annex17_entries rows (may be several)


def check_substance(conn: sqlite3.Connection, ec_no: str, cas_no: str | None) -> ListHits:
    """Look up one substance across all three lists.

    Primary key is EC number; CAS is used as a secondary probe when the
    EC lookup comes back empty (some BOMs carry CAS-only identities).
    """
    svhc = _one(
        conn,
        """
        SELECT s.ec_no, s.cas_no, s.name, e.reason, e.date_inclusion, e.decision
        FROM svhc_entries e JOIN substances s ON s.id = e.substance_id
        WHERE s.ec_no = ?
        """,
        (ec_no,),
    )
    a14 = _one(
        conn,
        """
        SELECT s.ec_no, s.cas_no, s.name, e.entry_no, e.date_inclusion, e.conditions
        FROM annex14_entries e JOIN substances s ON s.id = e.substance_id
        WHERE s.ec_no = ?
        """,
        (ec_no,),
    )
    a17 = _many(
        conn,
        """
        SELECT s.ec_no, s.cas_no, s.name, e.entry_no, e.conditions, e.first_published
        FROM annex17_entries e JOIN substances s ON s.id = e.substance_id
        WHERE s.ec_no = ?
        """,
        (ec_no,),
    )

    if svhc is None and a14 is None and not a17 and cas_no:
        # CAS-only fallback probe
        svhc = _one(
            conn,
            """
            SELECT s.ec_no, s.cas_no, s.name, e.reason, e.date_inclusion, e.decision
            FROM svhc_entries e JOIN substances s ON s.id = e.substance_id
            WHERE s.cas_no = ?
            """,
            (cas_no,),
        )
        a14 = _one(
            conn,
            """
            SELECT s.ec_no, s.cas_no, s.name, e.entry_no, e.date_inclusion, e.conditions
            FROM annex14_entries e JOIN substances s ON s.id = e.substance_id
            WHERE s.cas_no = ?
            """,
            (cas_no,),
        )
        a17 = _many(
            conn,
            """
            SELECT s.ec_no, s.cas_no, s.name, e.entry_no, e.conditions, e.first_published
            FROM annex17_entries e JOIN substances s ON s.id = e.substance_id
            WHERE s.cas_no = ?
            """,
            (cas_no,),
        )

    return ListHits(
        ec_no=ec_no,
        cas_no=cas_no,
        svhc=svhc,
        annex14=a14,
        annex17=a17 or None,
    )


def _one(conn: sqlite3.Connection, sql: str, params: tuple):
    row = conn.execute(sql, params).fetchone()
    return dict(row) if row else None


def _many(conn: sqlite3.Connection, sql: str, params: tuple) -> list[dict]:
    return [dict(r) for r in conn.execute(sql, params).fetchall()]
