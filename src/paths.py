"""Data and output locations. Override with BDB_RAW / BDB_PROC / BDB_FIG (e.g. on Kaggle)."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = Path(os.environ.get("BDB_RAW", ROOT / "data/raw/nfl-big-data-bowl-2027"))
PROC = Path(os.environ.get("BDB_PROC", ROOT / "data/processed"))
FIG = Path(os.environ.get("BDB_FIG", ROOT / "figures"))
