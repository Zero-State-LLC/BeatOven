from __future__ import annotations
from typing import Dict, Tuple
import numpy as np

def summarize_emotion_trajectory(arousal_series: list[float], valence_series: list[float]) -> Dict[str, float]:
    """
    Turns time series into stable descriptors:
    - drift
    - volatility
    - peakiness
    """
    if len(arousal_series) < 2:
        return {"arousal_drift": 0.0, "arousal_vol": 0.0, "arousal_peak": 0.0,
                "valence_drift": 0.0, "valence_vol": 0.0, "valence_peak": 0.0}

    a = np.array(arousal_series, dtype=np.float32)
    v = np.array(valence_series, dtype=np.float32)

    def pack(x: np.ndarray, name: str) -> Dict[str, float]:
        drift = float(x[-1] - x[0])
        vol = float(np.std(np.diff(x)))
        peak = float(np.max(x) - np.mean(x))
        return {f"{name}_drift": drift, f"{name}_vol": vol, f"{name}_peak": peak}

    out = {}
    out.update(pack(a, "arousal"))
    out.update(pack(v, "valence"))
    return out

def infer_era_from_heuristics(physical: Dict[str, float], semantic: Dict[str, object]) -> Tuple[Dict[str, float], float]:
    """
    Deterministic era prior.
    This is intentionally conservative: returns a distribution + confidence.
    You can replace this later with a trained model.
    """
    # Minimal weak signals:
    sharp = float(physical.get("sharpness", 0.0))
    sat = float(physical.get("sat_mean", 0.0))

    # Unknown remains unknown: with no usable signal, say so rather than guess
    # an era from the absence of sharpness (issue #22, operator decision B12).
    if sharp <= 1e-3 and sat <= 1e-3:
        return {"unknown": 1.0}, 0.05

    # Film-ish look: lower sharpness + moderate saturation -> older vibe (very weak)
    p_1990s = max(0.0, (0.6 - sharp)) * 0.6
    p_2000s = max(0.0, (0.5 - sharp)) * 0.4
    p_2010s = max(0.0, sharp - 0.4) * 0.6
    p_2020s = max(0.0, sharp - 0.6) * 0.7

    vec = {"1990s": p_1990s, "2000s": p_2000s, "2010s": p_2010s, "2020s": p_2020s}
    s = sum(vec.values())
    if s <= 1e-9:
        return {"unknown": 1.0}, 0.05
    vec = {k: v/s for k, v in vec.items()}

    # confidence rises if distribution is peaky
    conf = float(max(vec.values()))
    conf = max(0.05, min(0.65, conf))
    return vec, conf
