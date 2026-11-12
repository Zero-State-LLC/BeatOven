import pytest
from beatoven.media_intel.temporal import summarize_emotion_trajectory, infer_era_from_heuristics


def test_emotion_trajectory_empty():
    """Empty series should return zeros."""
    traj = summarize_emotion_trajectory([], [])
    assert traj["arousal_drift"] == 0.0
    assert traj["valence_drift"] == 0.0


def test_emotion_trajectory_single():
    """Single value should return zeros."""
    traj = summarize_emotion_trajectory([0.5], [0.5])
    assert traj["arousal_drift"] == 0.0
    assert traj["valence_drift"] == 0.0


def test_emotion_trajectory_drift():
    """Increasing series should show positive drift."""
    arousal = [0.2, 0.4, 0.6, 0.8]
    valence = [0.3, 0.3, 0.3, 0.3]

    traj = summarize_emotion_trajectory(arousal, valence)

    # Arousal increases
    assert traj["arousal_drift"] > 0.5
    # Valence stable
    assert abs(traj["valence_drift"]) < 0.1
    # Arousal has volatility
    assert traj["arousal_vol"] > 0.0


def test_infer_era_basic():
    """Era inference should return distribution and confidence."""
    physical = {"sharpness": 0.5, "sat_mean": 0.4}
    semantic = {}

    era_dist, conf = infer_era_from_heuristics(physical, semantic)

    # Should return dict of era labels
    assert isinstance(era_dist, dict)
    assert len(era_dist) > 0

    # Confidence in expected range
    assert 0.0 <= conf <= 1.0

    # Distribution should sum to ~1.0
    total = sum(era_dist.values())
    assert 0.95 <= total <= 1.05


def test_infer_era_unknown():
    """Very low features should return 'unknown'."""
    physical = {"sharpness": 0.0, "sat_mean": 0.0}
    semantic = {}

    era_dist, conf = infer_era_from_heuristics(physical, semantic)

    # Should have unknown
    assert "unknown" in era_dist
    # Low confidence
    assert conf < 0.2
