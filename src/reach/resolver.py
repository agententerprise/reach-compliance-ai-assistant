"""Substance name -> identity resolution.

The Resolver protocol is the seam where the fine-tuned 4B plugs in.
The StubResolver matches names directly against the substances table so
the deterministic pipeline is testable end-to-end before the model exists.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from enum import Enum


class Confidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    ABSTAIN = "abstain"


@dataclass(frozen=True)
class Resolution:
    query: str
    ec_no: str | None = None
    cas_no: str | None = None
    matched_name: str | None = None
    confidence: Confidence = Confidence.ABSTAIN

    @property
    def resolved(self) -> bool:
        return self.ec_no is not None and self.confidence in (
            Confidence.HIGH,
            Confidence.MEDIUM,
        )


class Resolver:
    """Interface implemented by every resolver (stub and model)."""

    def resolve(self, name: str) -> Resolution:
        raise NotImplementedError


class StubResolver(Resolver):
    """Exact / case-insensitive match against the substances table.

    Deterministic stand-in: proves the pipeline, defines the contract,
    and acts as the fallback when a model resolution comes back low.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._names: dict[str, sqlite3.Row] = {}
        for row in conn.execute("SELECT id, ec_no, cas_no, name FROM substances"):
            key = row["name"].strip().casefold()
            # first definition wins on duplicate names
            self._names.setdefault(key, row)

    def resolve(self, name: str) -> Resolution:
        key = name.strip().casefold()
        row = self._names.get(key)
        if row is None:
            return Resolution(query=name, confidence=Confidence.ABSTAIN)
        return Resolution(
            query=name,
            ec_no=row["ec_no"],
            cas_no=row["cas_no"],
            matched_name=row["name"],
            confidence=Confidence.HIGH,
        )
