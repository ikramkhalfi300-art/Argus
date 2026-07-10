"""Validation tests for the AgentOutput contract (Sprint 2.1.1).

Tests cover:
- Accept a fully valid, well-formed object
- Reject any output missing the evidence array
- Reject missing citations within evidence
- Reject invalid confidence values
- Reject out-of-range sub_score values
- Reject out-of-range data_completeness_pct values
"""

import pytest
from pydantic import ValidationError

from app.schemas.agent_output import AgentOutput, EvidenceItem


def _valid_output(**overrides) -> dict:
    base = {
        "agent_name": "test_agent",
        "pillar": "demand_strength",
        "sub_score": 75.0,
        "confidence": "High",
        "evidence": [{"claim": "The product has strong ad presence", "citation": "FB Ad Library — 15 active ads found"}],
        "data_completeness_pct": 90.0,
        "raw_findings": {"some_key": "some_value"},
    }
    base.update(overrides)
    return base


class TestAgentOutputValid:
    def test_accepts_valid_object(self):
        output = AgentOutput(**self._valid())
        assert output.agent_name == "market_saturation_agent"
        assert output.pillar == "competitive_saturation"
        assert output.sub_score == 82.0
        assert output.confidence == "Medium"
        assert len(output.evidence) == 1
        assert output.data_completeness_pct == 75.0
        assert output.raw_findings == {"active_advertiser_count": 5, "market_stage": "Growing"}

    def _valid(self):
        return {
            "agent_name": "market_saturation_agent",
            "pillar": "competitive_saturation",
            "sub_score": 82.0,
            "confidence": "Medium",
            "evidence": [{"claim": "5 active advertisers found", "citation": "FB Ad Library query result"}],
            "data_completeness_pct": 75.0,
            "raw_findings": {"active_advertiser_count": 5, "market_stage": "Growing"},
        }


class TestEvidenceValidation:
    def test_rejects_missing_evidence_array(self):
        payload = _valid_output()
        del payload["evidence"]
        with pytest.raises(ValidationError):
            AgentOutput(**payload)

    def test_rejects_empty_evidence_array(self):
        payload = _valid_output(evidence=[])
        with pytest.raises(ValidationError, match=".*List should have at least 1 item.*"):
            AgentOutput(**payload)

    def test_rejects_evidence_without_claim(self):
        payload = _valid_output(evidence=[{"citation": "some source"}])
        with pytest.raises(ValidationError):
            AgentOutput(**payload)

    def test_rejects_evidence_without_citation(self):
        payload = _valid_output(evidence=[{"claim": "some claim"}])
        with pytest.raises(ValidationError):
            AgentOutput(**payload)

    def test_rejects_empty_claim_string(self):
        payload = _valid_output(evidence=[{"claim": "", "citation": "source"}])
        with pytest.raises(ValidationError):
            AgentOutput(**payload)

    def test_rejects_empty_citation_string(self):
        payload = _valid_output(evidence=[{"claim": "claim", "citation": ""}])
        with pytest.raises(ValidationError):
            AgentOutput(**payload)

    def test_evidence_item_direct_validation(self):
        with pytest.raises(ValidationError):
            EvidenceItem(claim="", citation="source")


class TestConfidenceValidation:
    def test_rejects_invalid_confidence_lowcase(self):
        with pytest.raises(ValidationError):
            AgentOutput(**{"agent_name": "a", "pillar": "p", "sub_score": 50, "confidence": "low", "evidence": [{"claim": "c", "citation": "s"}], "data_completeness_pct": 50})

    def test_rejects_invalid_confidence_numeric(self):
        with pytest.raises(ValidationError):
            AgentOutput(**{"agent_name": "a", "pillar": "p", "sub_score": 50, "confidence": 3, "evidence": [{"claim": "c", "citation": "s"}], "data_completeness_pct": 50})

    def test_rejects_invalid_confidence_unknown_string(self):
        with pytest.raises(ValidationError):
            AgentOutput(**{"agent_name": "a", "pillar": "p", "sub_score": 50, "confidence": "VeryHigh", "evidence": [{"claim": "c", "citation": "s"}], "data_completeness_pct": 50})

    def test_accepts_low(self):
        output = AgentOutput(**{"agent_name": "a", "pillar": "p", "sub_score": 50, "confidence": "Low", "evidence": [{"claim": "c", "citation": "s"}], "data_completeness_pct": 50})
        assert output.confidence == "Low"

    def test_accepts_medium(self):
        output = AgentOutput(**{"agent_name": "a", "pillar": "p", "sub_score": 50, "confidence": "Medium", "evidence": [{"claim": "c", "citation": "s"}], "data_completeness_pct": 50})
        assert output.confidence == "Medium"

    def test_accepts_high(self):
        output = AgentOutput(**{"agent_name": "a", "pillar": "p", "sub_score": 50, "confidence": "High", "evidence": [{"claim": "c", "citation": "s"}], "data_completeness_pct": 50})
        assert output.confidence == "High"


class TestSubScoreValidation:
    def test_rejects_negative_sub_score(self):
        with pytest.raises(ValidationError):
            AgentOutput(**{"agent_name": "a", "pillar": "p", "sub_score": -1, "confidence": "Medium", "evidence": [{"claim": "c", "citation": "s"}], "data_completeness_pct": 50})

    def test_rejects_sub_score_above_100(self):
        with pytest.raises(ValidationError):
            AgentOutput(**{"agent_name": "a", "pillar": "p", "sub_score": 101, "confidence": "Medium", "evidence": [{"claim": "c", "citation": "s"}], "data_completeness_pct": 50})

    def test_accepts_zero(self):
        output = AgentOutput(**{"agent_name": "a", "pillar": "p", "sub_score": 0, "confidence": "Low", "evidence": [{"claim": "c", "citation": "s"}], "data_completeness_pct": 50})
        assert output.sub_score == 0.0

    def test_accepts_one_hundred(self):
        output = AgentOutput(**{"agent_name": "a", "pillar": "p", "sub_score": 100, "confidence": "High", "evidence": [{"claim": "c", "citation": "s"}], "data_completeness_pct": 50})
        assert output.sub_score == 100.0

    def test_accepts_float_value(self):
        output = AgentOutput(**{"agent_name": "a", "pillar": "p", "sub_score": 37.5, "confidence": "Medium", "evidence": [{"claim": "c", "citation": "s"}], "data_completeness_pct": 50})
        assert output.sub_score == 37.5


class TestDataCompletenessValidation:
    def test_rejects_negative_data_completeness(self):
        with pytest.raises(ValidationError):
            AgentOutput(**{"agent_name": "a", "pillar": "p", "sub_score": 50, "confidence": "Medium", "evidence": [{"claim": "c", "citation": "s"}], "data_completeness_pct": -0.1})

    def test_rejects_data_completeness_above_100(self):
        with pytest.raises(ValidationError):
            AgentOutput(**{"agent_name": "a", "pillar": "p", "sub_score": 50, "confidence": "Medium", "evidence": [{"claim": "c", "citation": "s"}], "data_completeness_pct": 100.1})

    def test_accepts_zero_completeness(self):
        output = AgentOutput(**{"agent_name": "a", "pillar": "p", "sub_score": 50, "confidence": "Low", "evidence": [{"claim": "c", "citation": "s"}], "data_completeness_pct": 0})
        assert output.data_completeness_pct == 0.0

    def test_accepts_full_completeness(self):
        output = AgentOutput(**{"agent_name": "a", "pillar": "p", "sub_score": 50, "confidence": "High", "evidence": [{"claim": "c", "citation": "s"}], "data_completeness_pct": 100})
        assert output.data_completeness_pct == 100.0
