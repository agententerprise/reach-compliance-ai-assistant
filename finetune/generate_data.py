"""Generate fine-tuning data using the local 27B teacher.

Task A: substance name -> identity resolution.
For each substance name, the teacher returns strict JSON:
    {"ec_no": "...", "cas_no": "...", "confidence": "high|medium|low"}

The teacher is prompted with the *actual* substances table as reference
context in batches, so labels come from the pinned ECHA data, not from
the model's parametric memory.

Usage:
    python generate_data.py --names data/substance_names.txt --out data/train.jsonl
    python generate_data.py --names data/substance_names.txt --out data/train.jsonl --limit 50  # smoke test
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

from openai import OpenAI

TEACHER_URL = "http://127.0.0.1:8080/v1"
TEACHER_MODEL = "/media/avinash/WindowsSSD/llms/ATX-Swift-1.5-Qwen3.8-27B-Uncensored-IQ4_XS-M.gguf"

SYSTEM_PROMPT = """You are a REACH substance identification expert.
Given a substance name (possibly noisy, abbreviated, or a synonym),
identify its EC number and CAS number from the reference list provided.

Respond with ONLY a JSON object, no markdown, no explanation:
{"ec_no": "NNN-NNN-N", "cas_no": "NNNNN-NN-N", "confidence": "high|medium|low"}

Rules:
- ec_no format: 7 digits as NNN-NNN-N. Use "" if unknown.
- cas_no format: standard CAS. Use "" if unknown.
- confidence "high": name is an exact or well-known synonym of one entry.
- confidence "medium": plausible match but ambiguous between entries.
- confidence "low": no reliable match in the reference list."""


def load_names(path: str) -> list[str]:
    names = [ln.strip() for ln in Path(path).read_text().splitlines() if ln.strip()]
    # dedupe, preserve order
    seen = set()
    out = []
    for n in names:
        if n.casefold() not in seen:
            seen.add(n.casefold())
            out.append(n)
    return out


def build_reference_batch(conn: sqlite3.Connection, names: list[str]) -> str:
    """Reference list of candidate entries: exact + fuzzy matches per name."""
    lines = []
    for name in names:
        like = f"%{name[:20]}%"
        rows = conn.execute(
            "SELECT ec_no, cas_no, name FROM substances WHERE name LIKE ? LIMIT 8",
            (like,),
        ).fetchall()
        if not rows:
            rows = conn.execute(
                "SELECT ec_no, cas_no, name FROM substances WHERE name LIKE ? LIMIT 8",
                (f"%{name.split()[-1][:15]}%"),
            ).fetchall()
        for r in rows:
            lines.append(f"{r[0]} | {r[1]} | {r[2]}")
    return "\n".join(dict.fromkeys(lines))  # dedupe, keep order


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--names", required=True, help="one substance name per line")
    ap.add_argument("--out", required=True, help="output JSONL")
    ap.add_argument("--db", default=str(Path(__file__).resolve().parents[1] / "data" / "reach.db"))
    ap.add_argument("--batch", type=int, default=25, help="names per teacher call")
    ap.add_argument("--limit", type=int, default=0, help="only process first N names (0 = all)")
    ap.add_argument("--resume", action="store_true", help="skip names already in --out")
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    names = load_names(args.names)
    if args.limit:
        names = names[: args.limit]

    done: set[str] = set()
    if args.resume and Path(args.out).exists():
        done = {
            json.loads(ln)["messages"][0]["content"].strip().casefold()
            for ln in Path(args.out).read_text().splitlines()
            if ln.strip()
        }
        print(f"resuming: {len(done)} already done")

    client = OpenAI(base_url=TEACHER_URL, api_key="local")
    out_f = open(args.out, "a" if args.resume else "w", encoding="utf-8")

    ok = fail = 0
    for i in range(0, len(names), args.batch):
        batch = [n for n in names[i : i + args.batch] if n.casefold() not in done]
        if not batch:
            continue
        reference = build_reference_batch(conn, batch)
        user_msg = (
            f"REFERENCE LIST (ec_no | cas_no | name):\n{reference}\n\n"
            f"Now identify each of these {len(batch)} names. "
            f"Return a JSON array with one object per name, in the same order:\n"
            + "\n".join(batch)
        )
        try:
            resp = client.chat.completions.create(
                model=TEACHER_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.0,
            )
            text = resp.choices[0].message.content.strip()
            # strip markdown fences if present
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            arr = json.loads(text)
            assert len(arr) == len(batch), f"expected {len(batch)}, got {len(arr)}"
            for name, obj in zip(batch, arr):
                example = {
                    "messages": [
                        {"role": "user", "content": f"Identify this substance: {name}"},
                        {
                            "role": "assistant",
                            "content": json.dumps(
                                {
                                    "ec_no": obj.get("ec_no", ""),
                                    "cas_no": obj.get("cas_no", ""),
                                    "confidence": obj.get("confidence", "low"),
                                }
                            ),
                        },
                    ]
                }
                out_f.write(json.dumps(example) + "\n")
            ok += len(batch)
        except Exception as e:
            fail += len(batch)
            print(f"batch {i // args.batch} failed: {e}", file=sys.stderr)
            time.sleep(2)
        out_f.flush()
        print(f"{min(i + args.batch, len(names))}/{len(names)} names labeled")

    out_f.close()
    print(f"done: {ok} labeled, {fail} failed -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
