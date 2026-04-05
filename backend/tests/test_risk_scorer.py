"""Unit tests for ml.risk.scorer.RiskScorer."""
import sys
from pathlib import Path

# Allow importing from ml/ and shared/ without installing the package
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from ml.risk.scorer import RiskScorer, RiskResult


@pytest.fixture
def scorer():
    return RiskScorer()


def test_all_zero_is_low(scorer):
    result = scorer.compute(0.0, 0.0, 0.0)
    assert result.tier == "low"
    assert result.score == 0.0


def test_low_tier_boundary(scorer):
    # score = 0.5*0.3 + 0.35*0.3 + 0.15*0.0 = 0.255 → low
    result = scorer.compute(0.3, 0.3, 0.0)
    assert result.tier == "low"
    assert result.score < 0.4


def test_moderate_tier(scorer):
    # score = 0.5*0.5 + 0.35*0.3 + 0.15*0.0 = 0.355 — still low
    # Use higher values: 0.5*0.6 + 0.35*0.4 + 0.15*0.0 = 0.44 → moderate
    result = scorer.compute(0.6, 0.4, 0.0)
    assert result.tier == "moderate"
    assert 0.4 <= result.score < 0.6


def test_high_tier(scorer):
    # 0.5*0.8 + 0.35*0.5 + 0.15*0.0 = 0.575 → but still moderate
    # Use: 0.5*0.8 + 0.35*0.7 + 0.15*0.0 = 0.645 → high
    result = scorer.compute(0.8, 0.7, 0.0)
    assert result.tier == "high"
    assert 0.6 <= result.score < 0.8


def test_crisis_tier(scorer):
    # 0.5*1.0 + 0.35*1.0 + 0.15*1.0 = 1.0 → crisis
    result = scorer.compute(1.0, 1.0, 1.0)
    assert result.tier == "crisis"
    assert result.score >= 0.8


def test_clamps_above_one(scorer):
    result = scorer.compute(2.0, 2.0, 2.0)
    assert result.score <= 1.0


def test_clamps_below_zero(scorer):
    result = scorer.compute(-1.0, -1.0, -1.0)
    assert result.score >= 0.0


def test_weights_sum_correctly(scorer):
    # Only anomaly contributes: 0.5*1.0 = 0.5
    result = scorer.compute(1.0, 0.0, 0.0)
    assert abs(result.score - 0.5) < 0.001

    # Only sentiment: 0.35*1.0 = 0.35
    result = scorer.compute(0.0, 1.0, 0.0)
    assert abs(result.score - 0.35) < 0.001

    # Only survey decline: 0.15*1.0 = 0.15
    result = scorer.compute(0.0, 0.0, 1.0)
    assert abs(result.score - 0.15) < 0.001


def test_result_is_risk_result_dataclass(scorer):
    result = scorer.compute(0.5, 0.5, 0.5)
    assert isinstance(result, RiskResult)
    assert hasattr(result, "score")
    assert hasattr(result, "tier")
    assert hasattr(result, "anomaly_score")
    assert hasattr(result, "sentiment_score")
    assert hasattr(result, "survey_decline")


def test_score_is_rounded(scorer):
    result = scorer.compute(0.333333, 0.666666, 0.111111)
    # Score should be rounded to 4 decimal places
    assert result.score == round(result.score, 4)
