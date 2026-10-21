"""Writeup figures from Phase 4/5 outputs.

Usage: PYTHONPATH=$PWD python -P -m src.figures
Writes figures/*.png.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src import models as M
from src.features.combine import MEI_WEIGHTS

from src.paths import FIG

A = M.PROC / "analysis"

SURFACE, INK, INK2, GRID = "#0c2a1f", "#f0efec", "#c3c2b7", "#2b4a3e"
# dark-mode categorical slots 1-4 (validated on SURFACE)
BLUE, ORANGE, AQUA, YELLOW = "#3987e5", "#d95926", "#199e70", "#c98500"
MODEL_STYLE = {"M1 traditional": ("Traditional (stopwatch)", BLUE, "o"),
               "M2 tracking": ("Tracking (learned weights)", ORANGE, "D"),
               "M3 hybrid": ("Hybrid", AQUA, "s"),
               "M2b MEI (fixed weights)": ("MEI, writeup weights", YELLOW, "^")}
OUTCOME_LABEL = {("DL", "get_off_eb"): "DL get-off", ("DL", "pressure_rate_eb"): "DL pressure rate",
                 ("DL", "sack_rate_eb"): "DL sack rate", ("DB", "db_closing_speed_eb"): "DB closing speed",
                 ("WR", "separation_eb"): "WR separation", ("OL", "peak_pressure_prob_eb"): "OL pressure prob."}

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "text.color": INK, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.edgecolor": GRID, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False, "font.family": "DejaVu Sans",
    "font.size": 11, "axes.titlesize": 14, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "legend.frameon": False, "lines.linewidth": 2,
})


def title(fig, main, sub):
    fig.text(0.02, 0.965, main, fontsize=16, fontweight="bold", color=INK, va="top")
    fig.text(0.02, 0.905, sub, fontsize=11, color=INK2, va="top")


def save(fig, name):
    FIG.mkdir(exist_ok=True)
    fig.savefig(FIG / name, dpi=200)
    plt.close(fig)
    print("saved", FIG / name)


def trend(ax, x, y, color):
    ok = np.isfinite(x) & np.isfinite(y)
    b = np.polyfit(x[ok], y[ok], 1)
    xs = np.linspace(x[ok].min(), x[ok].max(), 50)
    ax.plot(xs, np.polyval(b, xs), color=INK2, lw=2, ls="--", zorder=2)


def scatter(ax, x, y, color):
    ax.scatter(x, y, s=46, color=color, edgecolor=SURFACE, linewidth=1.5, zorder=3)
    trend(ax, np.asarray(x, float), np.asarray(y, float), color)


def fig_coverage():
    c = pd.read_csv(A / "coverage.csv").iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 4.6))
    fig.subplots_adjust(left=0.33, right=0.93, top=0.8, bottom=0.12)
    colors = [ORANGE if m.startswith("Tracking") else BLUE for m in c.metric]
    ax.barh(c.metric, c.share * 100, color=colors, height=0.62, edgecolor=SURFACE, linewidth=2)
    for i, (s, n) in enumerate(zip(c.share, c.n)):
        ax.text(s * 100 + 1.5, i, f"{s:.0%}  (n={n})", va="center", color=INK, fontsize=10)
    ax.set_xlim(0, 118)
    ax.set_xlabel("Share of the 510 Combine players with the metric (%)")
    ax.grid(axis="y", visible=False)
    title(fig, "Tracking measures every player", "Nearly two in three prospects skip the official three-cone or shuttle; tracked drills cover them all.")
    save(fig, "fig1_coverage.png")


def fig_transfer():
    d = pd.read_csv(A / "dl_players.csv")
    d["index"] = (d["index"] - d["index"].mean()) / d["index"].std()
    t = pd.read_csv(A / "transfer.csv").set_index("outcome")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.8))
    fig.subplots_adjust(left=0.08, right=0.98, top=0.72, bottom=0.14, wspace=0.28)
    g = d[d.n_get_off >= 50]
    scatter(axes[0], g["index"], g.get_off_eb, ORANGE)
    axes[0].invert_yaxis()
    axes[0].set_ylabel("NFL get-off time (s, quicker ↑)")
    r = t.loc["get_off_eb"]
    axes[0].set_title(f"Trained on: get-off\nρ = {-r.rho:.2f}  [95% CI {-r.hi:.2f}, {-r.lo:.2f}]", fontsize=12)
    p = d[d.n_pressure_rate >= 50]
    scatter(axes[1], p["index"], p.pressure_rate_eb * 100, ORANGE)
    axes[1].set_ylabel("NFL pressure rate (%, shrunk estimate)")
    r = t.loc["pressure_rate_eb"]
    axes[1].set_title(f"Never trained on: pressure rate\nρ = {r.rho:.2f}  [95% CI {r.lo:.2f}, {r.hi:.2f}]", fontsize=12)
    for ax in axes:
        ax.set_xlabel("DL Explosiveness Index (out-of-sample, z-score)")
    title(fig, "Combine explosiveness transfers to the pass rush",
          "Index learned from Combine tracking on two draft classes, scored on the third (n = 82 / 79 DL).")
    save(fig, "fig2_transfer.png")


def fig_smoothness():
    d = pd.read_csv(A / "dl_players.csv")
    a = pd.read_csv(M.PROC / "component_assoc.csv")
    r = a[(a.position == "DL") & (a.outcome == "pressure_rate_eb") & (a.feature == "smoothness")].iloc[0]
    p = d[d.n_pressure_rate >= 50]
    fig, ax = plt.subplots(figsize=(9, 4.8))
    fig.subplots_adjust(left=0.1, right=0.97, top=0.8, bottom=0.14)
    scatter(ax, p.smoothness, p.pressure_rate_eb * 100, YELLOW)
    ax.set_xlabel("Combine movement smoothness (drill-standardised; smoother →)")
    ax.set_ylabel("NFL pressure rate (%, shrunk estimate)")
    ax.text(0.98, 0.94, f"ρ = {r.rho:.2f}\nρ given draft slot = {r.partial_rho_pick:.2f}\nn = {int(r.n)}",
            transform=ax.transAxes, ha="right", va="top", color=INK, fontsize=11)
    title(fig, "The smoothness paradox", "Smoother Combine movers generate fewer NFL pressures. Explosive movement is variable movement.")
    save(fig, "fig3_smoothness.png")


def fig_models():
    c = pd.read_csv(A / "model_comparison.csv")
    tasks = list(OUTCOME_LABEL)
    fig, ax = plt.subplots(figsize=(9, 5.4))
    fig.subplots_adjust(left=0.2, right=0.97, top=0.74, bottom=0.12)
    offsets = dict(zip(MODEL_STYLE, [0.27, 0.09, -0.09, -0.27]))
    for model, (label, color, marker) in MODEL_STYLE.items():
        for i, (pos, out) in enumerate(tasks):
            r = c[(c.position == pos) & (c.outcome == out) & (c.model == model)].iloc[0]
            y = len(tasks) - 1 - i + offsets[model]
            ax.plot([r.lo, r.hi], [y, y], color=color, lw=2, solid_capstyle="round")
            ax.scatter(r.rho, y, s=60, color=color, marker=marker, edgecolor=SURFACE, linewidth=1.5, zorder=3,
                       label=label if i == 0 else None)
    ax.axvline(0, color=INK2, lw=1)
    ax.set_yticks(range(len(tasks)))
    ax.set_yticklabels([OUTCOME_LABEL[t] for t in tasks][::-1])
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Out-of-sample Spearman ρ, predicted vs. actual (95% bootstrap CI)")
    ax.legend(loc="lower center", bbox_to_anchor=(0.45, 1.0), ncol=4, fontsize=9.5, handletextpad=0.3, columnspacing=1.2)
    title(fig, "Where Combine movement predicts NFL performance",
          "Leave-one-draft-class-out ridge models. Strong for defensive line, weak or absent elsewhere.")
    save(fig, "fig4_models.png")


def fig_weights():
    w = pd.read_csv(A / "learned_weights.csv")
    w = w[w.position == "DL"].set_index("component").weight
    prior = pd.Series(MEI_WEIGHTS)
    names = {"accel_eff": "Acceleration", "decel_ctrl": "Deceleration", "cod_eff": "Change of direction",
             "smoothness": "Smoothness", "recovery_acc": "Recovery"}
    order = list(names)[::-1]
    y = np.arange(len(order))
    fig, ax = plt.subplots(figsize=(8, 4.8))
    fig.subplots_adjust(left=0.24, right=0.95, top=0.74, bottom=0.13)
    ax.barh(y + 0.19, prior[order], height=0.36, color=BLUE, edgecolor=SURFACE, linewidth=2, label="Writeup (a priori)")
    ax.barh(y - 0.19, w[order], height=0.36, color=ORANGE, edgecolor=SURFACE, linewidth=2, label="Learned for DL (get-off)")
    for yy, v in zip(y - 0.19, w[order]):
        ax.text(v + (0.012 if v >= 0 else -0.012), yy, f"{v:+.2f}", va="center", ha="left" if v >= 0 else "right", fontsize=9.5, color=INK)
    ax.axvline(0, color=INK2, lw=1)
    ax.set_yticks(y)
    ax.set_yticklabels([names[c] for c in order])
    ax.grid(axis="y", visible=False)
    ax.set_xlim(-0.42, 0.58)
    ax.set_xlabel("Share of index weight (sign = direction of effect)")
    ax.legend(loc="lower center", bbox_to_anchor=(0.4, 1.0), ncol=2)
    title(fig, "What the data says the MEI should weigh", "For defensive linemen, acceleration dominates and smoothness counts against.")
    save(fig, "fig5_weights.png")


def main():
    fig_coverage()
    fig_transfer()
    fig_smoothness()
    fig_models()
    fig_weights()


if __name__ == "__main__":
    main()
