"""Phase 4: does Combine tracking predict NFL outcomes beyond the stopwatch and draft slot?

Usage: PYTHONPATH=$PWD python -P -m src.models [--perms N]
Writes data/processed/model_results.csv and data/processed/component_assoc.csv.
"""
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.impute import SimpleImputer
from sklearn.linear_model import RidgeCV
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.features.combine import COMPONENTS

from src.paths import PROC, RAW
SEED = 2027
UNDRAFTED_PICK = 262
N_BOOT = 1000

TRADITIONAL = ["forty", "ten_yd_split", "vertical", "broad_jump", "combine_weight", "combine_height"]
TRACKING = COMPONENTS                  # learned weights
MEI = ["mei"]                          # writeup's fixed weights
DRAFT = ["log_pick", "undrafted"]

# (position, outcome, min plays, plays column); outcomes chosen in docs/outcome_notes.md
TASKS = [
    ("WR", "separation_eb", 50, "n_separation"), ("WR", "yprr_eb", 50, "n_yprr"),
    ("TE", "separation_eb", 50, "n_separation"), ("TE", "yprr_eb", 50, "n_yprr"),
    ("OL", "peak_pressure_prob_eb", 100, "n_peak_pressure_prob"),
    ("OL", "pressure_allowed_rate_eb", 100, "n_pressure_allowed_rate"),
    ("DL", "get_off_eb", 50, "n_get_off"), ("DL", "pressure_rate_eb", 50, "n_pressure_rate"),
    ("DL", "sack_rate_eb", 50, "n_sack_rate"),
    ("DB", "db_closing_speed_eb", 15, "n_db_closing_speed"), ("DB", "db_break_accel_eb", 15, "n_db_break_accel"),
] + [(p, o, 0, None) for p in ["WR", "TE", "OL", "DL", "DB"] for o in ["snaps_per_season", "games_active_share"]]

MODELS = {
    "M0 draft only": DRAFT,
    "M1 traditional": TRADITIONAL,
    "M2 tracking": TRACKING,
    "M2b MEI (fixed weights)": MEI,
    "M3 hybrid": TRADITIONAL + TRACKING,
    "M1 + draft": TRADITIONAL + DRAFT,
    "M2 + draft": TRACKING + DRAFT,
    "M3 + draft": TRADITIONAL + TRACKING + DRAFT,
}


def load():
    feats = pd.read_parquet(PROC / "combine_features.parquet")
    outc = pd.read_parquet(PROC / "outcomes.parquet").drop(columns=["draft_year", "combine_position"])
    trad = pd.read_csv(RAW / "combine_results.csv")[["nfl_id"] + TRADITIONAL]
    df = feats.merge(trad, on="nfl_id").merge(outc, on="nfl_id")
    df["undrafted"] = df.draft_overall_pick.isna().astype(float)
    df["log_pick"] = np.log(df.draft_overall_pick.fillna(UNDRAFTED_PICK))
    return df


def model():
    return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                         RidgeCV(alphas=np.logspace(-2, 4, 25)))


def cv_predict(X, y, groups):
    """Leave-one-draft-class-out out-of-sample predictions."""
    pred = np.full(len(y), np.nan)
    for g in np.unique(groups):
        tr, te = groups != g, groups == g
        pred[te] = model().fit(X[tr], y[tr]).predict(X[te])
    return pred


def boot_ci(y, preds_a, preds_b=None, rng=None):
    """Bootstrap 95% CI of OOS R^2 (or of the R^2 difference a - b)."""
    n, stats = len(y), []
    for _ in range(N_BOOT):
        i = rng.integers(0, n, n)
        r = r2_score(y[i], preds_a[i])
        if preds_b is not None:
            r -= r2_score(y[i], preds_b[i])
        stats.append(r)
    return np.percentile(stats, [2.5, 97.5])


def perm_p(X, y, groups, observed, n_perm, rng):
    """Permutation p-value: shuffle the outcome within draft class, re-run CV."""
    if n_perm == 0:
        return np.nan
    hits = 0
    for _ in range(n_perm):
        yp = y.copy()
        for g in np.unique(groups):
            m = groups == g
            yp[m] = rng.permutation(yp[m])
        hits += r2_score(yp, cv_predict(X, yp, groups)) >= observed
    return (hits + 1) / (n_perm + 1)


def run(n_perm):
    df = load()
    rng = np.random.default_rng(SEED)
    rows, assoc = [], []
    for pos, outcome, min_n, ncol in TASKS:
        d = df[(df.combine_position == pos) & df[outcome].notna()]
        if ncol:
            d = d[d[ncol] >= min_n]
        y, groups = d[outcome].to_numpy(float), d.draft_year.to_numpy()
        preds = {}
        for name, cols in MODELS.items():
            X = d[cols].to_numpy(float)
            preds[name] = p = cv_predict(X, y, groups)
            r2 = r2_score(y, p)
            lo, hi = boot_ci(y, p, rng=rng)
            test_perm = name in ("M2 tracking", "M2b MEI (fixed weights)", "M1 traditional")
            rows.append(dict(position=pos, outcome=outcome, model=name, n=len(y), r2=r2, r2_lo=lo, r2_hi=hi,
                             mae=mean_absolute_error(y, p), rho=spearmanr(y, p).statistic,
                             perm_p=perm_p(X, y, groups, r2, n_perm if test_perm else 0, rng)))
        for a, b in [("M3 hybrid", "M1 traditional"), ("M3 + draft", "M1 + draft"), ("M2 + draft", "M0 draft only")]:
            lo, hi = boot_ci(y, preds[a], preds[b], rng=rng)
            rows.append(dict(position=pos, outcome=outcome, model=f"Δ {a} − {b}", n=len(y),
                             r2=r2_score(y, preds[a]) - r2_score(y, preds[b]), r2_lo=lo, r2_hi=hi))
        # single-feature associations, raw and holding draft slot fixed
        for f in TRACKING + ["mei", "cod_asymmetry", "top_speed"] + TRADITIONAL:
            x = d[f]
            ok = x.notna()
            if ok.sum() < 15:
                continue
            rho, p = spearmanr(x[ok], y[ok])
            resid = lambda v: v - np.polyval(np.polyfit(d.log_pick[ok], v, 1), d.log_pick[ok])
            prho, pp = spearmanr(resid(x[ok].rank()), resid(pd.Series(y[ok.to_numpy()]).rank().to_numpy()))
            assoc.append(dict(position=pos, outcome=outcome, feature=f, n=int(ok.sum()),
                              rho=rho, p=p, partial_rho_pick=prho, partial_p=pp))
        print(f"{pos} {outcome}: n={len(y)}", flush=True)
    return pd.DataFrame(rows), pd.DataFrame(assoc)


def main():
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    n_perm = int(sys.argv[sys.argv.index("--perms") + 1]) if "--perms" in sys.argv else 200
    res, assoc = run(n_perm)
    res.to_csv(PROC / "model_results.csv", index=False)
    assoc.to_csv(PROC / "component_assoc.csv", index=False)


if __name__ == "__main__":
    main()
