#!/usr/bin/env python3
"""Ingest ECHA list CSVs into SQLite.

Schema:
  substances        — canonical substance identities (EC/CAS/name)
  svhc_entries      — Candidate List (SVHC) rows
  annex14_entries   — Annex XIV authorisation rows
  annex17_entries   — Annex XVII restriction rows

Usage: python3 ingest.py [data_dir] [db_path]
"""
import csv
import os
import re
import sqlite3
import sys

DATA_DIR = sys.argv[1] if len(sys.argv) > 1 else "data"
DB_PATH = sys.argv[2] if len(sys.argv) > 2 else os.path.join(DATA_DIR, "reach.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS substances (
    id          INTEGER PRIMARY KEY,
    ec_no       TEXT,                 -- e.g. 231-791-2
    cas_no      TEXT,                 -- e.g. 13463-67-7
    name        TEXT,
    description TEXT,
    UNIQUE(ec_no, cas_no)
);
CREATE INDEX IF NOT EXISTS idx_sub_ec  ON substances(ec_no);
CREATE INDEX IF NOT EXISTS idx_sub_cas ON substances(cas_no);
CREATE INDEX IF NOT EXISTS idx_sub_name ON substances(name);

CREATE TABLE IF NOT EXISTS svhc_entries (
    id              INTEGER PRIMARY KEY,
    substance_id    INTEGER REFERENCES substances(id),
    reason          TEXT,
    date_inclusion  TEXT,
    decision        TEXT,
    remarks         TEXT
);

CREATE TABLE IF NOT EXISTS annex14_entries (
    id              INTEGER PRIMARY KEY,
    substance_id    INTEGER REFERENCES substances(id),
    entry_no        TEXT,
    date_inclusion  TEXT,
    conditions      TEXT,
    remarks         TEXT
);

CREATE TABLE IF NOT EXISTS annex17_entries (
    id              INTEGER PRIMARY KEY,
    substance_id    INTEGER REFERENCES substances(id),
    entry_no        TEXT,
    conditions      TEXT,
    appendices      TEXT,
    first_published TEXT,
    remarks         TEXT
);

CREATE TABLE IF NOT EXISTS metadata (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


def clean(v: str) -> str:
    return re.sub(r"\s+", " ", (v or "").strip())


def read_rows(path: str):
    """Yield (header, [rows]) from an ECHA TSV with banner lines."""
    with open(path, encoding="utf-8") as fh:
        rows = [r for r in csv.reader(fh, delimiter="\t")]
    header = None
    for r in rows:
        if sum(1 for c in r if c.strip()) > 3:
            header = [clean(c) for c in r]
            break
    if header is None:
        raise ValueError(f"no header found in {path}")
    data = []
    for r in rows:
        if r == header or sum(1 for c in r if c.strip()) < 2:
            continue
        data.append(dict(zip(header, [clean(c) for c in r] + [""] * (len(header) - len(r)))))
    return header, data


def get_substance(conn, ec, cas, name, desc):
    cur = conn.execute(
        "SELECT id FROM substances WHERE ec_no=? AND cas_no=?", (ec or None, cas or None)
    )
    row = cur.fetchone()
    if row:
        return row[0]
    conn.execute(
        "INSERT INTO substances (ec_no, cas_no, name, description) VALUES (?,?,?,?)",
        (ec or None, cas or None, name, desc),
    )
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    counts = {}

    # --- SVHC Candidate List ---
    _, rows = read_rows(os.path.join(DATA_DIR, "svhc_candidate_list.csv"))
    n = 0
    for r in rows:
        sid = get_substance(conn, r.get("EC No."), r.get("CAS No."),
                            r.get("Substance name"), r.get("Description"))
        conn.execute(
            "INSERT INTO svhc_entries (substance_id, reason, date_inclusion, decision, remarks)"
            " VALUES (?,?,?,?,?)",
            (sid, r.get("Reason for inclusion"), r.get("Date of inclusion"),
             r.get("Decision"), r.get("Remarks")),
        )
        n += 1
    counts["svhc"] = n

    # --- Annex XIV ---
    _, rows = read_rows(os.path.join(DATA_DIR, "annex_xiv_authorisation.csv"))
    n = 0
    for r in rows:
        sid = get_substance(conn, r.get("EC No."), r.get("CAS No."),
                            r.get("Substance name"), r.get("Description"))
        conn.execute(
            "INSERT INTO annex14_entries (substance_id, entry_no, date_inclusion, conditions, remarks)"
            " VALUES (?,?,?,?,?)",
            (sid, r.get("Entry no."), r.get("Date of inclusion in Authorisation List From"),
             r.get("Conditions"), r.get("Remarks")),
        )
        n += 1
    counts["annex14"] = n

    # --- Annex XVII ---
    _, rows = read_rows(os.path.join(DATA_DIR, "annex_xvii_restrictions.csv"))
    n = 0
    for r in rows:
        sid = get_substance(conn, r.get("EC No."), r.get("CAS No."),
                            r.get("Substance name"), r.get("Description"))
        conn.execute(
            "INSERT INTO annex17_entries (substance_id, entry_no, conditions, appendices,"
            " first_published, remarks) VALUES (?,?,?,?,?,?)",
            (sid, r.get("Entry no."), r.get("Conditions"), r.get("Appendices"),
             r.get("First published"), r.get("Remarks")),
        )
        n += 1
    counts["annex17"] = n

    for k, v in counts.items():
        conn.execute("INSERT OR REPLACE INTO metadata VALUES (?,?)", (k, str(v)))
    conn.execute("INSERT OR REPLACE INTO metadata VALUES ('export_date','2026-11-09')")
    conn.commit()

    total_sub = conn.execute("SELECT COUNT(*) FROM substances").fetchone()[0]
    print(f"DB: {DB_PATH}")
    print(f"substances: {total_sub}")
    for k, v in counts.items():
        print(f"{k}_entries: {v}")
    conn.close()


if __name__ == "__main__":
    main()
