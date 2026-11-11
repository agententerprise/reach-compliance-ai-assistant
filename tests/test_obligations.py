"""Unit tests for the deterministic obligation rules."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reach.check import ListHits
from reach.obligations import (
    SVHC_COMMUNICATION_THRESHOLD_PCT,
    derive_obligations,
)


def make_hits(svhc=None, a14=None, a17=None):
    return ListHits(ec_no="000-000-0", cas_no="000-00-0", svhc=svhc, annex14=a14, annex17=a17)


SVHC_ROW = {
    "ec_no": "203-777-6", "cas_no": "111-65-9", "name": "n-hexane",
    "reason": "CMR", "date_inclusion": "2002-06-20", "decision": "n/a",
}
A14_ROW = {
    "ec_no": "247-148-4", "cas_no": "3194-55-6", "name": "HBCD",
    "entry_no": "46", "date_inclusion": "2013-01-12", "conditions": "n/a",
}
A17_ROW = {
    "ec_no": "200-831-0", "cas_no": "74-85-1", "name": "Chloroethene",
    "entry_no": "26", "conditions": "n/a", "first_published": "2020-02-07",
}


def test_svhc_above_threshold_triggers_art33():
    obs = derive_obligations(make_hits(svhc=SVHC_ROW), 0.5)
    codes = [o.code for o in obs]
    assert "SVHC_ART33" in codes
    assert "0.1%" in obs[0].detail or "0.50%" in obs[0].detail
    assert "SVHC Candidate List" in obs[0].citation


def test_svhc_exactly_at_threshold_triggers():
    obs = derive_obligations(make_hits(svhc=SVHC_ROW), SVHC_COMMUNICATION_THRESHOLD_PCT)
    assert any(o.code == "SVHC_ART33" for o in obs)


def test_svhc_below_threshold_no_duty():
    obs = derive_obligations(make_hits(svhc=SVHC_ROW), 0.05)
    assert any(o.code == "SVHC_BELOW_THRESHOLD" for o in obs)
    assert not any(o.code == "SVHC_ART33" for o in obs)


def test_svhc_unknown_concentration_flagged():
    obs = derive_obligations(make_hits(svhc=SVHC_ROW), None)
    assert any(o.code == "SVHC_CONCENTRATION_UNKNOWN" for o in obs)


def test_annex14_always_authorisation():
    obs = derive_obligations(make_hits(a14=A14_ROW), 0.001)
    assert any(o.code == "ANNEX14_AUTHORISATION" for o in obs)
    a14 = [o for o in obs if o.code == "ANNEX14_AUTHORISATION"][0]
    assert "entry 46" in a14.citation


def test_annex17_one_obligation_per_entry():
    obs = derive_obligations(make_hits(a17=[A17_ROW, dict(A17_ROW, entry_no="99")]), 1.0)
    a17 = [o for o in obs if o.code == "ANNEX17_RESTRICTION"]
    assert len(a17) == 2


def test_no_hits_no_obligations():
    assert derive_obligations(make_hits(), 50.0) == []


def test_citations_always_present():
    obs = derive_obligations(make_hits(svhc=SVHC_ROW, a14=A14_ROW, a17=[A17_ROW]), 1.0)
    assert all(o.citation for o in obs)
