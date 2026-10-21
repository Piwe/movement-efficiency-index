"""Assemble the public Kaggle notebook from the project's source files.

Usage: python notebooks/build_notebook.py
Writes notebooks/explosiveness-transfers.ipynb. The %%writefile cells embed src/ verbatim,
so the notebook and the repository cannot drift apart.
"""
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks/explosiveness-transfers.ipynb"
MODULES = ["src/__init__.py", "src/paths.py", "src/features/__init__.py", "src/features/kinematics.py",
           "src/features/combine.py", "src/outcomes.py", "src/models.py", "src/analysis.py", "src/figures.py",
           "tests/__init__.py", "tests/test_kinematics.py"]

md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
cells = [
    md("# Explosiveness Transfers, Smoothness Misleads\n"
       "### Rebuilding the Movement Efficiency Index (MEI) with Combine sensor tracking\n\n"
       "**NFL Big Data Bowl 2027: reproducible analysis notebook.**\n\n"
       "This notebook rebuilds every number and figure in the writeup from the raw competition data:\n\n"
       "1. Movement features and the Movement Efficiency Index (MEI) from 10 Hz Combine tracking\n"
       "2. Regular-season NFL outcomes, including DB reaction metrics from game tracking\n"
       "3. Leave-one-draft-class-out models with bootstrap CIs and permutation tests\n"
       "4. The DL transfer test, learned MEI weights, reliability and validation tables\n"
       "5. The writeup figures\n\n"
       "Runtime is about 20 minutes on a Kaggle CPU session, most of it the 200-permutation model run."),
    code("import os\nfrom pathlib import Path\n\n"
         "KAGGLE_INPUT = Path('/kaggle/input/nfl-big-data-bowl-2027')\n"
         "if KAGGLE_INPUT.exists():\n"
         "    os.environ.setdefault('BDB_RAW', str(KAGGLE_INPUT))\n"
         "os.environ.setdefault('BDB_PROC', 'processed')\n"
         "os.environ.setdefault('BDB_FIG', 'figures')\n"
         "for d in ['src/features', 'tests', os.environ['BDB_PROC'], os.environ['BDB_FIG']]:\n"
         "    Path(d).mkdir(parents=True, exist_ok=True)\n"
         "print({k: os.environ[k] for k in ['BDB_RAW', 'BDB_PROC', 'BDB_FIG']})"),
    md("## Source code\n"
       "The analysis is a small package, written out here so the notebook is self-contained."),
]
for rel in MODULES:
    cells.append(code(f"%%writefile {rel}\n" + (ROOT / rel).read_text()))

cells += [
    md("## 1. Unit tests for the movement metrics\n"
       "Synthetic sprints, cuts and plant-and-reverse moves with known answers."),
    code("!python -m pytest -q tests"),
    md("## 2. Combine movement features and the MEI"),
    code("import warnings\nwarnings.filterwarnings('ignore')\n"
         "import pandas as pd\npd.set_option('display.width', 200, 'display.max_columns', 30)\n\n"
         "from src.features import combine\ncombine.main()\n"
         "pd.read_parquet(combine.OUT / 'combine_features.parquet').describe().round(2)"),
    code("from src import analysis\nanalysis.validation().round(2)"),
    md("## 3. NFL regular-season outcomes\nIncludes a pass over ~2 GB of game tracking for DB man-coverage throws."),
    code("from src import outcomes\noutcomes.main()"),
    code("analysis.reliability().round(2)"),
    md("## 4. Models: traditional vs. tracking vs. hybrid\n"
       "Ridge regression, leave-one-draft-class-out CV, 1,000 bootstrap resamples, 200 permutations."),
    code("import sys\nfrom src import models\nsys.argv = ['models', '--perms', os.environ.get('BDB_PERMS', '200')]\nmodels.main()\n"
         "res = pd.read_csv(models.PROC / 'model_results.csv')\n"
         "res[~res.model.str.startswith('Δ')].pivot_table(index=['position', 'outcome'], columns='model', values='rho').round(2)"),
    md("## 5. Transfer test, learned weights, coverage"),
    code("analysis.main()"),
    md("## 6. Figures"),
    code("from IPython.display import Image, display\nfrom src import figures\nfigures.main()\n"
         "for f in sorted(figures.FIG.glob('fig*.png')):\n    display(Image(filename=str(f), width=900))"),
]

nb = nbf.v4.new_notebook(cells=cells, metadata={
    "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
    "language_info": {"name": "python"}})
nbf.write(nb, OUT)
print("wrote", OUT, f"({len(cells)} cells)")
