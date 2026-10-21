# NFL Big Data Bowl 2027: Explosiveness Transfers, Smoothness Misleads

Open Track entry linking 10 Hz Combine sensor tracking to NFL regular-season performance.
The writeup is `writeup.md`; its figures are in `figures/` and its thumbnail is `thumbnail.png`.

## Layout

| Path | Purpose |
|---|---|
| `src/features/kinematics.py` | Per-attempt signals, cut detection and MEI components |
| `src/features/combine.py` | Player-level Combine features and the MEI |
| `src/outcomes.py` | NFL outcomes with empirical-Bayes shrinkage; DB game-tracking pass |
| `src/models.py` | Leave-one-draft-class-out ridge models, bootstrap CIs, permutations |
| `src/analysis.py` | Validation, reliability, transfer test, learned weights, coverage |
| `src/figures.py` | Writeup figures |
| `src/paths.py` | Data/output locations (`BDB_RAW`, `BDB_PROC`, `BDB_FIG`) |
| `notebooks/build_notebook.py` | Builds the Kaggle notebook from `src/` |
| `kaggle_kernel/` | Notebook + metadata for `kaggle kernels push` |
| `docs/` | Data audit, feature, outcome and model notes |
| `assets/story_images.py`, `assets/thumbnail.py` | Story sequence (`screenshots/`) and `thumbnail.png`: `python3 assets/story_images.py screenshots` |

## Reproduce

```bash
python3 -m venv --system-site-packages .venv && .venv/bin/pip install kaggle statsmodels pytest nbformat
.venv/bin/kaggle competitions download nfl-big-data-bowl-2027 -p data/raw   # then extract the zip
export PYTHONPATH=$PWD
.venv/bin/python -m pytest -q tests
.venv/bin/python -P -m src.features.combine
.venv/bin/python -P -m src.outcomes
.venv/bin/python -P -m src.models --perms 200
.venv/bin/python -P -m src.analysis
.venv/bin/python -P -m src.figures
```

Rebuild the notebook after changing `src/`: `.venv/bin/python -P notebooks/build_notebook.py`.
