import numpy as np
import pytest

from src.features.kinematics import DT, attempt_features


def sprint(vmax=10.0, tau=0.8, secs=5.0):
    t = np.arange(0, secs, DT)
    v = vmax * (1 - np.exp(-t / tau))
    x = np.cumsum(v) * DT + 10
    return x, np.zeros_like(x), v


def cut_run(turn_deg=90.0, v0=7.0, vmin=2.5, left=True):
    """Run straight, slow into a cut, turn, re-accelerate."""
    speeds = np.r_[np.linspace(0, v0, 15), np.full(10, v0), np.linspace(v0, vmin, 8),
                   np.full(3, vmin), np.linspace(vmin, v0, 12), np.full(10, v0)]
    turn = np.radians(turn_deg) * (1 if left else -1)
    heading = np.r_[np.zeros(30), np.linspace(0, turn, 8), np.full(len(speeds) - 38, turn)]
    x = np.cumsum(speeds * np.cos(heading)) * DT
    y = np.cumsum(speeds * np.sin(heading)) * DT
    return x, y, speeds


def test_straight_sprint_has_no_cuts():
    f = attempt_features(*sprint())
    assert f.cuts == []
    assert f.peak_speed == pytest.approx(10.0, rel=0.03)


def test_faster_starter_has_higher_accel_eff():
    quick = attempt_features(*sprint(tau=0.5))
    slow = attempt_features(*sprint(tau=1.2))
    assert quick.accel_eff > slow.accel_eff


def test_cut_detected_with_turn_size_and_sign():
    left = attempt_features(*cut_run(left=True))
    right = attempt_features(*cut_run(left=False))
    assert len(left.cuts) == 1 and len(right.cuts) == 1
    assert left.cuts[0].turn == pytest.approx(90, abs=15)
    assert right.cuts[0].turn == pytest.approx(-90, abs=15)


def test_harder_stop_scores_higher_decel_control():
    sharp = attempt_features(*cut_run(vmin=1.5))
    soft = attempt_features(*cut_run(vmin=4.5))
    assert sharp.decel_ctrl > soft.decel_ctrl


def test_smaller_speed_loss_means_more_efficient_cut():
    efficient = attempt_features(*cut_run(vmin=5.0))
    wasteful = attempt_features(*cut_run(vmin=2.0))
    assert efficient.cuts[0].cod_eff > wasteful.cuts[0].cod_eff


def test_noise_reduces_smoothness():
    x, y, v = sprint()
    rng = np.random.default_rng(0)
    noisy = attempt_features(x, y, v + rng.normal(0, 0.4, len(v)))
    assert attempt_features(x, y, v).smoothness > noisy.smoothness


def test_plant_and_reverse_detected():
    v = np.r_[np.linspace(0, 6, 10), np.linspace(6, 0.2, 6), np.linspace(0.2, 6, 10), np.full(10, 6.0)]
    sign = np.r_[np.ones(16), -np.ones(20)]
    x = np.cumsum(v * sign) * DT
    f = attempt_features(x, np.zeros_like(x), v)
    assert len(f.cuts) == 1
    assert abs(f.cuts[0].turn) == pytest.approx(180, abs=10)


def test_stationary_attempt_returns_none():
    z = np.zeros(30)
    assert attempt_features(z, z, z) is None
