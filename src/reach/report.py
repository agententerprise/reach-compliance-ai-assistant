"""Report assembly: Markdown + JSON with citations and pinned list versions."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .db import list_version
from .scan import ArticleFinding


def _fmt_conc(v: float | None) -> str:
    return f"{v:g}%" if v is not None else "not stated"


def to_markdown(findings: list[ArticleFinding], bom_path: str, versions: dict[str, str]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    n_flag = sum(1 for f in findings if f.obligations)
    n_review = sum(1 for f in findings if f.needs_review)
    n_clean = sum(1 for f in findings if f.clean)

    lines = [
        "# REACH Compliance Report",
        "",
        f"- **BOM:** `{bom_path}` ({len(findings)} substance rows)",
        f"- **Generated:** {now}",
        "- **Lists:** "
        + ", ".join(f"{k} = {v}" for k, v in sorted(versions.items()))
        + " (pinned)",
        "",
        "## Summary",
        "",
        f"| Outcome | Rows |",
        f"|---|---|",
        f"| Obligations triggered | {n_flag} |",
        f"| Needs human review | {n_review} |",
        f"| Clean | {n_clean} |",
        "",
        "## Findings",
        "",
    ]

    for f in findings:
        ident = f"{f.ec_no or '?'}" + (f" / CAS {f.cas_no}" if f.cas_no else "")
        lines.append(f"### {f.substance} — `{ident}` @ {_fmt_conc(f.concentration_pct)}")
        lines.append("")
        if f.needs_review:
            lines.append(f"> **NEEDS REVIEW:** {f.review_reason}")
            lines.append("")
        if not f.obligations and not f.needs_review:
            lines.append("No REACH list hits. Clean.")
            lines.append("")
            continue
        for o in f.obligations:
            lines.append(f"- **{o.title}**")
            lines.append(f"  - {o.detail}")
            lines.append(f"  - _Source: {o.citation}_")
        lines.append("")

    lines += [
        "## Scope & limitations",
        "",
        "- Registration tonnage tiers are not derived: REACH registration is",
        "  per-substance per-manufacturer aggregated across all articles, which a",
        "  single BOM cannot establish.",
        "- Annex XVII entries are flagged for review; entry-specific conditions",
        "  (concentration limits, exemptions, dates) require reading the entry text.",
        "- Concentrations are taken as stated in the BOM (weight percent).",
        "",
    ]
    return "\n".join(lines)


def to_json(findings: list[ArticleFinding], bom_path: str, versions: dict[str, str]) -> str:
    payload = {
        "bom": bom_path,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "list_versions": versions,
        "findings": [asdict(f) for f in findings],
    }
    return json.dumps(payload, indent=2)


def write_reports(
    findings: list[ArticleFinding],
    bom_path: str,
    versions: dict[str, str],
    out_dir: str | Path,
    stem: str,
) -> tuple[Path, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    md = out / f"{stem}.md"
    js = out / f"{stem}.json"
    md.write_text(to_markdown(findings, bom_path, versions), encoding="utf-8")
    js.write_text(to_json(findings, bom_path, versions), encoding="utf-8")
    return md, js
