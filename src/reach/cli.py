"""CLI entry point.

Usage:
    python -m reach.cli --bom data/demo_bom.csv --resolver stub --out reports/
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .db import connect, list_version
from .report import write_reports
from .resolver import StubResolver
from .scan import parse_bom, scan_bom


def build_resolver(name: str, conn):
    if name == "stub":
        return StubResolver(conn)
    if name == "model":
        # Fine-tuned 4B via PydanticAI — lands in build step 4.
        raise SystemExit(
            "model resolver not built yet (step 4); use --resolver stub"
        )
    raise SystemExit(f"unknown resolver: {name}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="reach")
    ap.add_argument("--bom", required=True, help="BOM CSV (article, substance, concentration_pct)")
    ap.add_argument("--db", default=None, help="path to reach.db (default: data/reach.db)")
    ap.add_argument("--resolver", default="stub", choices=["stub", "model"])
    ap.add_argument("--out", default="reports", help="output directory")
    args = ap.parse_args(argv)

    conn = connect(args.db)
    versions = list_version(conn)
    resolver = build_resolver(args.resolver, conn)

    rows = parse_bom(args.bom)
    findings = scan_bom(conn, resolver, rows)

    stem = Path(args.bom).stem
    md, js = write_reports(findings, args.bom, versions, args.out, stem)

    n_flag = sum(1 for f in findings if f.obligations)
    n_review = sum(1 for f in findings if f.needs_review)
    print(f"scanned {len(findings)} rows: {n_flag} with obligations, {n_review} need review")
    print(f"report: {md}")
    print(f"json:   {js}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
