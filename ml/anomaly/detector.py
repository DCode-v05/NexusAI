"""IsolationForest-based behavioral anomaly detector.

Loads a persisted model if available, otherwise trains on synthetic normal-behavior
data and saves the model for future use.
"""
import asyncio
import os
import pickle
from pathlib import Path

import numpy as np
from sklearn.ensemble import IsolationForest

from ml.anomaly.features import BehaviorFeatureExtractor

MODEL_PATH = Path(__file__).parent / "models" / "isolation_forest.pkl"
MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)


def _generate_synthetic_normal(n: int = 2000) -> np.ndarray:
    """Generate synthetic "healthy" student behavior for cold-start training."""
    rng = np.random.default_rng(42)
    return np.column_stack([
        rng.uniform(0, 0.2, n),   # session_gap_days (low = good)
        rng.uniform(0, 0.1, n),   # survey_skip_streak (low = good)
        rng.uniform(0.3, 0.8, n), # avg_session_length (moderate)
        rng.uniform(0, 0.2, n),   # assignment_delay_hrs (low = good)
        rng.uniform(0.3, 0.7, n), # chat_initiation_freq (moderate)
        rng.uniform(-0.1, 0.1, n),# mood_score_trend (stable)
        rng.uniform(0, 0.3, n),   # login_hour_variance (low = good)
    ]).astype(np.float32)


def _train_and_save() -> IsolationForest:
    data = _generate_synthetic_normal()
    model = IsolationForest(contamination=0.05, random_state=42, n_estimators=100)
    model.fit(data)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    return model


def _load_or_train() -> IsolationForest:
    if MODEL_PATH.exists():
        with open(MODEL_PATH, "rb") as f:
            return pickle.load(f)
    return _train_and_save()


class AnomalyDetector:
    _model: IsolationForest | None = None

    @classmethod
    def _get_model(cls) -> IsolationForest:
        if cls._model is None:
            cls._model = _load_or_train()
        return cls._model

    def _predict_sync(self, feature_vector: np.ndarray) -> float:
        model = self._get_model()
        # decision_function returns negative = anomalous
        score = model.decision_function(feature_vector)[0]
        # Normalize to [0, 1] where 1 = most anomalous
        normalized = max(0.0, min(1.0, -score + 0.5))
        return float(normalized)

    async def predict(self, feature_vector: np.ndarray) -> float:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._predict_sync, feature_vector)

    async def predict_from_log(self, log) -> float:
        extractor = BehaviorFeatureExtractor()
        vec = extractor.extract(log)
        return await self.predict(vec)
