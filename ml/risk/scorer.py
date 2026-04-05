"""Weighted risk scorer — the core decision function of NexusAI.

weighted_risk = 0.5 * anomaly + 0.35 * sentiment + 0.15 * survey_decline

Tiers:
  < 0.4  → low       (no action)
  0.4–0.6 → moderate  (wellbeing agent generates empathetic message)
  0.6–0.8 → high      (counselor encouraged + iCall)
  >= 0.8 → crisis    (three-signal gate + counselor alert + iCall)
"""
from dataclasses import dataclass
from shared.utils import clamp


@dataclass
class RiskResult:
    score: float
    tier: str  # "low" | "moderate" | "high" | "crisis"
    anomaly_score: float
    sentiment_score: float
    survey_decline: float


class RiskScorer:
    def compute(
        self,
        anomaly_score: float,
        sentiment_score: float,
        survey_decline: float,
    ) -> RiskResult:
        a = clamp(anomaly_score, 0.0, 1.0)
        s = clamp(sentiment_score, 0.0, 1.0)
        d = clamp(survey_decline, 0.0, 1.0)

        score = 0.50 * a + 0.35 * s + 0.15 * d
        score = clamp(score, 0.0, 1.0)

        if score >= 0.8:
            tier = "crisis"
        elif score >= 0.6:
            tier = "high"
        elif score >= 0.4:
            tier = "moderate"
        else:
            tier = "low"

        return RiskResult(
            score=round(score, 4),
            tier=tier,
            anomaly_score=round(a, 4),
            sentiment_score=round(s, 4),
            survey_decline=round(d, 4),
        )
