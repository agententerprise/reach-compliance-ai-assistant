"""Verify teacher-generated labels against reach.db.

Every training example's ec_no/cas_no must exist in the substances table.
Examples that fail verification are quarantined for inspection, not
silently dropped — a systematic failure here means the generator prompt
needs work, not the data.

Usage:
    python verify_data.py --in data/train.jsonl --out data/train_verified.jsonl
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--quarantine", default=None, help="where to write failed examples")
    ap.add_argument("--db", default=str(Path(__file__).resolve().parents[1] / "data" / "reach.db"))
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    known = {
        (r[0], r[1]) for r in conn.execute("SELECT ec_no, cas_no FROM substances")
    }
    known_ec = {r[0] for r in conn.execute("SELECT ec_no FROM substances")}
    known_cas = {r[0] for r in conn.execute("SELECT cas_no FROM substances")}

    def is_known(ec: str, cas: str) -> bool:
        # ECHA uses '-' for substances without an EC number
        ec_ok = (ec in ("", "-") and cas in known_cas) or (ec in known_ec and (not cas or (ec, cas) in known))
        return ec_ok

    ok, bad, empty = 0, [], []
    with open(args.inp) as f, open(args.out, "w") as good, open(args.quarantine or "/dev/null", "w") as q:
        for ln, line in enumerate(f, 1):
            if not line.strip():
                continue
            ex = json.loads(line)
            name = ex["messages"][0]["content"].replace("Identify this substance: ", "")
            label = json.loads(ex["messages"][1]["content"])
            ec, cas = label.get("ec_no", ""), label.get("cas_no", "")

            if not ec and not cas:
                # teacher abstained — keep only if confidence is low (that's a valid training signal)
                if label.get("confidence") == "low":
                    good.write(line)
                    ok += 1
                else:
                    bad.append((ln, name, "abstained but not low-confidence", label))
                continue

            if is_known(ec, cas):
                good.write(line)
                ok += 1
            else:
                bad.append((ln, name, f"ec={ec} cas={cas} not in db", label))
                q.write(line)

    print(f"verified: {ok} ok, {len(bad)} quarantined")
    for ln, name, why, label in bad[:10]:
        print(f"  line {ln}: {name!r} -> {why}")
    if len(bad) > 10:
        print(f"  ... and {len(bad) - 10} more (see quarantine file)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
