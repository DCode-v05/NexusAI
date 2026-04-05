"""Extract a 7-feature numpy array from a BehaviorLog row."""
import numpy as np
from dataclasses import dataclass


@dataclass
class BehaviorVector:
    session_gap_days: float
    survey_skip_streak: float
    avg_session_length: float
    assignment_delay_hrs: float
    chat_initiation_freq: float
    mood_score_trend: float
    login_hour_variance: float


FEATURE_NAMES = [
    "session_gap_days",
    "survey_skip_streak",
    "avg_session_length",
    "assignment_delay_hrs",
    "chat_initiation_freq",
    "mood_score_trend",
    "login_hour_variance",
]

# Simple normalization bounds (domain knowledge priors)
_BOUNDS = {
    "session_gap_days": (0, 30),
    "survey_skip_streak": (0, 14),
    "avg_session_length": (0, 120),
    "assignment_delay_hrs": (0, 48),
    "chat_initiation_freq": (0, 10),
    "mood_score_trend": (-5, 5),
    "login_hour_variance": (0, 12),
}


def _normalize(value: float, lo: float, hi: float) -> float:
    if hi == lo:
        return 0.0
    return max(0.0, min(1.0, (value - lo) / (hi - lo)))


class BehaviorFeatureExtractor:
    def extract(self, log) -> np.ndarray:
        """Accept a BehaviorLog ORM object or a dict and return shape (1, 7)."""
        if hasattr(log, "__dict__"):
            vec = {k: getattr(log, k, 0.0) for k in FEATURE_NAMES}
        else:
            vec = {k: log.get(k, 0.0) for k in FEATURE_NAMES}

        features = [
            _normalize(float(vec[k]), *_BOUNDS[k])
            for k in FEATURE_NAMES
        ]
        return np.array([features], dtype=np.float32)
