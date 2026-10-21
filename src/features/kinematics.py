"""Per-attempt movement signals and MEI components from 10 Hz tracking.

Units: yards, seconds. Heading is computed from smoothed x/y velocity
(counter-clockwise positive), so a positive heading change is a left turn.
"""
from dataclasses import dataclass, field

import numpy as np
from scipy.signal import find_peaks, savgol_filter

DT = 0.1
ACTIVE_SPEED = 0.5      # yd/s: movement onset / end of activity
CUT_WINDOW = 8          # frames each side used for direction of travel
CUT_MIN_TURN = 35.0     # deg: minimum heading change to count as a cut
CUT_MIN_SPEED = 1.0     # yd/s: mean velocity needed on both sides of a cut
CUT_SPACING = 8         # frames: minimum gap between two cuts
APPROACH = 15           # frames: look-back for approach speed
DECEL_THRESH = -1.0     # yd/s^2: deceleration episode threshold
DECEL_MIN_DV = 1.5      # yd/s: minimum speed drop for an episode
RECOVER_FRAC = 0.9      # share of pre-cut speed that counts as recovered


@dataclass
class Signals:
    t: np.ndarray
    v: np.ndarray        # smoothed speed
    at: np.ndarray       # signed tangential acceleration
    at_resid: np.ndarray  # acceleration minus its smooth trend
    vx: np.ndarray
    vy: np.ndarray


@dataclass
class Cut:
    turn: float          # signed heading change, degrees (+ = left)
    v_pre: float         # approach speed
    v_min: float         # slowest speed through the cut
    elapsed: float       # slowdown start -> recovery
    dist: float          # distance covered over `elapsed`
    time_lost: float
    cod_eff: float
    recovery_acc: float


@dataclass
class AttemptFeatures:
    peak_speed: float = np.nan
    accel_eff: float = np.nan
    decel_ctrl: float = np.nan
    smoothness: float = np.nan
    cuts: list = field(default_factory=list)


def _savgol(x, window, deriv=0):
    window = min(window, len(x) - (1 - len(x) % 2))
    if window < 5:
        return np.gradient(x, DT) if deriv else x.astype(float)
    return savgol_filter(x, window, 2, deriv=deriv, delta=DT)


def signals(x, y, s):
    """Trim to active movement and derive smoothed kinematic signals."""
    x, y, s = map(np.asarray, (x, y, s))
    moving = np.flatnonzero(s > ACTIVE_SPEED)
    if len(moving) < 5:
        return None
    lo, hi = max(moving[0] - 2, 0), min(moving[-1] + 3, len(s))
    x, y, s = x[lo:hi], y[lo:hi], s[lo:hi]
    v = np.clip(_savgol(s, 7), 0, None)
    at = _savgol(s, 7, deriv=1)
    at_resid = _savgol(s, 5, deriv=1) - _savgol(s, 15, deriv=1)
    vx, vy = _savgol(x, 7, deriv=1), _savgol(y, 7, deriv=1)
    return Signals(np.arange(len(v)) * DT, v, at, at_resid, vx, vy)


def _runs(mask):
    """(start, end_exclusive) index pairs of True runs."""
    d = np.diff(np.r_[0, mask.astype(int), 0])
    return list(zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)))


def acceleration_efficiency(sg):
    """0.9 x peak speed / time from onset to reaching 0.9 x peak speed."""
    vmax = sg.v.max()
    onset = np.argmax(sg.v > ACTIVE_SPEED)
    reach = onset + np.argmax(sg.v[onset:] >= 0.9 * vmax)
    t = max(sg.t[reach] - sg.t[onset], DT)
    return vmax, 0.9 * vmax / t


def deceleration_control(sg):
    """Largest deceleration episode: speed lost / distance travelled (1/s)."""
    best = None
    for a, b in _runs(sg.at < DECEL_THRESH):
        b = min(b, len(sg.v) - 1)
        dv = sg.v[a] - sg.v[b]
        if dv >= DECEL_MIN_DV:
            dist = np.trapezoid(sg.v[a:b + 1], dx=DT)
            if best is None or dv > best[0]:
                best = (dv, dv / max(dist, 0.05))
    return np.nan if best is None else best[1]


def smoothness(sg):
    """Negative log RMS of acceleration around its trend (higher = smoother)."""
    return -np.log(np.sqrt(np.mean(sg.at_resid ** 2)) + 1e-6)


def turn_profile(sg):
    """Signed angle (deg, + = left) between mean velocity before and after each frame.

    Comparing whole windows rather than instantaneous heading keeps plant-and-reverse
    cuts, where speed passes through zero, and rounded cuts on the same footing.
    """
    k, n = CUT_WINDOW, len(sg.v)
    ang = np.zeros(n)
    for i in range(k, n - k):
        ax, ay = sg.vx[i - k:i].mean(), sg.vy[i - k:i].mean()
        bx, by = sg.vx[i + 1:i + k + 1].mean(), sg.vy[i + 1:i + k + 1].mean()
        if np.hypot(ax, ay) >= CUT_MIN_SPEED and np.hypot(bx, by) >= CUT_MIN_SPEED:
            ang[i] = np.degrees(np.arctan2(ax * by - ay * bx, ax * bx + ay * by))
    return ang


def cuts(sg):
    """Detect changes of direction and score each one."""
    out = []
    ang = turn_profile(sg)
    peaks, _ = find_peaks(np.abs(ang), height=CUT_MIN_TURN, distance=CUT_SPACING)
    n = len(sg.v)
    for j, i in enumerate(peaks):
        lo = max(i - APPROACH, 0)
        nxt = peaks[j + 1] if j + 1 < len(peaks) else n
        v_pre = sg.v[lo:i + 1].max()
        # slowdown starts at the last frame before the cut still near approach speed
        near = np.flatnonzero(sg.v[lo:i + 1] >= RECOVER_FRAC * v_pre)
        a = lo + near[-1]
        i_min = a + int(np.argmin(sg.v[a:min(i + CUT_WINDOW, n - 1) + 1]))
        # recovered = regains 90% of approach speed; on short legs the next cut can come
        # first, in which case recovery ends at the fastest frame before that cut
        seg = sg.v[i_min:max(nxt, i_min + 1)]
        after = np.flatnonzero(seg >= RECOVER_FRAC * v_pre)
        i_rec = i_min + (after[0] if len(after) else int(np.argmax(seg)))
        dist = np.trapezoid(sg.v[a:i_rec + 1], dx=DT)
        time_lost = max(sg.t[i_rec] - sg.t[a] - dist / v_pre, 0.05)
        rec_t = max(sg.t[i_rec] - sg.t[i_min], DT)
        out.append(Cut(turn=float(ang[i]), v_pre=float(v_pre), v_min=float(sg.v[i_min]),
                       elapsed=float(sg.t[i_rec] - sg.t[a]), dist=float(dist), time_lost=float(time_lost),
                       cod_eff=float(abs(ang[i]) / time_lost),
                       recovery_acc=float((sg.v[i_rec] - sg.v[i_min]) / rec_t)))
    return out


def attempt_features(x, y, s):
    sg = signals(x, y, s)
    if sg is None:
        return None
    f = AttemptFeatures()
    f.peak_speed, f.accel_eff = acceleration_efficiency(sg)
    f.decel_ctrl = deceleration_control(sg)
    f.smoothness = smoothness(sg)
    f.cuts = cuts(sg)
    return f
