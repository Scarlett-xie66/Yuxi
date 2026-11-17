"""Build the five figures for the Blog 9 article (result/figures, 300 dpi).

figure_timeline     split dates and the tradable forecast window
figure_model        schematic from inputs to position
figure_behaviour    forecast dispersion and forecast-versus-outcome scatter
figure1_accuracy    relative accuracy with bootstrap intervals
figure2_investment  wealth paths and drawdowns
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
from evaluate_investment import simulate, MAIN_BPS  # noqa: E402

RES = ROOT / "result" / "tables"
FIGS = ROOT / "result" / "figures"
FIGS.mkdir(parents=True, exist_ok=True)

BLUE, ORANGE, GREEN, GRAY, INK = "#202020", "#b65b3c", "#2f7f92", "#9aa0a6", "#222222"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": "#666", "axes.labelcolor": INK,
                     "xtick.color": INK, "ytick.color": INK, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 300})


def fm(x):
    return f"{x:+.1f}".replace("-", "\u2212")


def figure1():
    tm = pd.read_csv(RES / "test_metrics.csv").set_index("model")
    inf = pd.read_csv(RES / "inference.csv")
    gaps = {r.comparison.split(" vs")[0]: (r.boot_lo_pct, r.boot_hi_pct)
            for r in inf.itertuples()
            if isinstance(r.boot_lo_pct, float) and r.comparison.endswith("historical mean")}

    rows = [("Regularized boosting", 0, GREEN),
            ("Basic boosting", 1, ORANGE),
            ("Five-session mean", 2, "#9aa0a6")]

    fig, ax = plt.subplots(figsize=(7.4, 3.1))
    for name, ypos, col in rows:
        val = float(tm.loc[name, "mse_relative_pct"])
        lo, hi = gaps[name]
        ax.plot([lo, hi], [ypos, ypos], color=col, lw=4, solid_capstyle="round",
                alpha=.35, zorder=3)
        ax.scatter([val], [ypos], s=80, color=col, zorder=4)
        if hi < 6:                      # label to the right, clear of the zero line
            ax.annotate(f"{val:+.2f}% worse   (95% interval {fm(lo)} to {fm(hi)})",
                        (hi + 0.5, ypos), ha="left", va="center", fontsize=8.6, color=INK)
        else:
            ax.annotate(f"{val:+.2f}% worse", (val, ypos), textcoords="offset points",
                        xytext=(0, 15), ha="center", fontsize=9.5, fontweight="bold", color=INK)
            ax.annotate(f"95% interval {fm(lo)} to {fm(hi)}", (val, ypos),
                        textcoords="offset points", xytext=(0, -24), ha="center",
                        fontsize=8.2, color="#666")

    ax.axvline(0, color=INK, lw=1.3, zorder=1)
    ax.annotate("0 = historical mean, no model needed", (0.5, 2.62), ha="left", va="center",
                fontsize=8.2, color="#555",
                bbox=dict(facecolor="white", edgecolor="none", pad=1.5))
    ax.set_xlim(-3.5, 45)
    ax.set_ylim(-0.62, 2.72)
    ax.set_yticks([0, 1, 2])
    ax.set_yticklabels(["Revised\nmodel", "Original\nmodel", "Five-session\nmean"], fontsize=9)
    ax.set_xlabel("Mean squared error relative to the historical mean (%, lower is better)", fontsize=9)
    ax.set_xticks([0, 10, 20, 30, 40])
    ax.grid(axis="x", color="#ececec", lw=.8)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(FIGS / "figure1_accuracy.png", bbox_inches="tight")
    plt.close(fig)


def figure2():
    fc = pd.read_csv(ROOT / "data" / "processed" / "forecasts.csv", parse_dates=["date"])
    y = fc["realized_return_pp"].values
    pos = {"Continuous index exposure": np.ones_like(y),
           "Basic boosting": (fc["forecast_basic"].values > 0).astype(float),
           "Regularized boosting": (fc["forecast_regularized"].values > 0).astype(float)}
    col = {"Continuous index exposure": BLUE, "Basic boosting": ORANGE,
           "Regularized boosting": GREEN}
    lab = {"Continuous index exposure": "Hold the index throughout",
           "Basic boosting": "Original model (classroom configuration)",
           "Regularized boosting": "Revised model"}

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.6, 3.3), gridspec_kw={"width_ratios": [1.25, 1]})
    wealth, drawdown = {}, {}
    for k, p in pos.items():
        w = simulate(y, p, MAIN_BPS)["wealth"] * 100
        wealth[k] = w
        drawdown[k] = (w / np.maximum.accumulate(np.concatenate([[100.0], w]))[1:] - 1) * 100
        a1.plot(fc["date"], w, color=col[k], lw=1.5 if k != "Continuous index exposure" else 2.0,
                label=lab[k])
        a2.plot(fc["date"], drawdown[k], color=col[k], lw=1.4)

    trough_idx = int(np.argmin(drawdown["Continuous index exposure"]))
    trough_date = fc["date"].iloc[trough_idx]
    a1.axvline(trough_date, color=GRAY, lw=1, ls="--", zorder=1)
    a2.axvline(trough_date, color=GRAY, lw=1, ls="--", zorder=1)

    a1.set_title("Growth of $100, after 5-basis-point costs", fontsize=10, loc="left")
    a2.set_title("Fall from previous peak", fontsize=10, loc="left")
    a1.set_ylabel("Portfolio value ($, start = 100)")
    a2.set_ylabel("Percent below the earlier peak")
    for ax in (a1, a2):
        ax.tick_params(axis="x", labelsize=8.4)
        ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
        ax.grid(color="#ececec", lw=.8)
        ax.set_axisbelow(True)
    a1.legend(frameon=False, fontsize=8.4, loc="upper left", bbox_to_anchor=(0, 1.02))
    fig.tight_layout()
    fig.savefig(FIGS / "figure2_investment.png", bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------- schematics

def _box(ax, x, y, w, h, text, fc, ec="none", fs=8.6, color="#1f1f1f", weight="normal"):
    from matplotlib.patches import FancyBboxPatch
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.012",
                                linewidth=0, facecolor=fc))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=color,
            linespacing=1.35, fontweight=weight)


def _arrow(ax, x0, y0, x1, y1, color="#888888"):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.1, shrinkA=2, shrinkB=2))


def figure_timeline():
    fig = plt.figure(figsize=(7.4, 2.15))
    gs = fig.add_gridspec(2, 1, height_ratios=[1, 1.15], hspace=.30)

    ax = fig.add_subplot(gs[0])
    segs = [("Fit the model\n2017–2021 · 1,239", "2017-01-01", "2021-12-31", "#7f97a8"),
            ("Choose settings\n2022–2023 · 501", "2022-01-01", "2023-12-31", "#c1a68a"),
            ("Evaluate once\n2024–2025 · 502", "2024-01-01", "2025-12-31", "#2f7f92")]
    for lab, a, b, c in segs:
        a, b = pd.Timestamp(a), pd.Timestamp(b)
        ax.barh(0, b - a, left=a, height=.62, color=c, linewidth=0)
        ax.text(a + (b - a) / 2, 0, lab, ha="center", va="center", fontsize=7.6,
                color="white", linespacing=1.4)
    ax.set_ylim(-.45, .45)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.set_xlim(pd.Timestamp("2016-10-01"), pd.Timestamp("2026-02-01"))
    for side in ("left", "right", "top", "bottom"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="x", color="#f0f0f0", lw=.7)
    ax.set_axisbelow(True)
    ax.set_title("Train on the past, choose on 2022–2023, look at 2024–2025 once",
                 fontsize=9.4, loc="left", color=INK, pad=6)

    ax2 = fig.add_subplot(gs[1])
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 1.5)
    ax2.axis("off")
    bw, bh, y = 2.55, .48, .72
    boxes = [(.05, "#e8eef2", "close t\nall nine inputs known"),
             (3.55, "#f4e7cf", "close t+1\norder placed here"),
             (7.05, "#dbecef", "close t+2\nreturn realised")]
    for x, fc, t in boxes:
        _box(ax2, x, y, bw, bh, t, fc, fs=7.2)
    for x0, x1 in [(.05 + bw, 3.55), (3.55 + bw, 7.05)]:
        _arrow(ax2, x0 + .05, y + bh / 2, x1 - .05, y + bh / 2)
    xs, xt = 3.90, 9.25
    ax2.plot([xs, xt], [y + bh + .20] * 2, color="#b65b3c", lw=.9)
    ax2.plot([xs, xs], [y + bh + .20, y + bh + .09], color="#b65b3c", lw=.9)
    ax2.plot([xt, xt], [y + bh + .20, y + bh + .09], color="#b65b3c", lw=.9)
    ax2.text((xs + xt) / 2, y + bh + .26, "the return being forecast", ha="center", va="bottom",
             fontsize=7.2, color="#b65b3c")
    ax2.text(.05, .22, "Nothing from the session in between enters the forecast.",
             ha="left", va="center", fontsize=7.2, color="#5c6166")
    fig.savefig(FIGS / "figure_timeline.png", bbox_inches="tight")
    plt.close(fig)


def figure_model():
    fig, ax = plt.subplots(figsize=(7.4, 1.45))
    ax.set_xlim(0, 10)
    ax.set_ylim(.55, 1.45)
    ax.axis("off")
    yc, bh = 1.04, .56

    stages = [(.05, 1.75, "9 inputs\nfrom prices", "#e8eef2"),
              (1.95, 1.35, "100 trees,\n1 question each", "#f4e7cf"),
              (3.45, 1.25, "sum of\ncorrections", "#eef2f5"),
              (4.85, 1.45, "+ historical\nmean", "#eef2f5"),
              (6.45, 1.30, "forecast,\nin points", "#f4e7cf"),
              (7.90, 2.05, "long if > 0,\ncash if not", "#dfe7ee")]
    for x, w, text, fc in stages:
        _box(ax, x, yc - bh / 2, w, bh, text, fc, fs=7.4)
    for i in range(len(stages) - 1):
        x0 = stages[i][0] + stages[i][1]
        x1 = stages[i + 1][0]
        _arrow(ax, x0 + .02, yc, x1 - .02, yc)
    ax.text(3.60, .64, "× learning rate 0.1 (original) / 0.03 (revised)",
            ha="center", va="center", fontsize=7.2, color="#6d7378")
    fig.savefig(FIGS / "figure_model.png", bbox_inches="tight")
    plt.close(fig)


def figure_behaviour():
    fc = pd.read_csv(ROOT / "data" / "processed" / "forecasts.csv", parse_dates=["date"])
    fb = pd.read_csv(RES / "forecast_behaviour.csv").set_index("model")
    y = fc["realized_return_pp"].values
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.6, 2.5), gridspec_kw={"width_ratios": [1.1, 1]})

    rows = [("Actual returns", y, "#9aa0a6", 2),
            ("Original model", fc["forecast_basic"].values, ORANGE, 1),
            ("Revised model", fc["forecast_regularized"].values, GREEN, 0)]
    for lab, v, c, yy in rows:
        lo, hi = np.percentile(v, [5, 95])
        a1.plot([lo, hi], [yy, yy], color=c, lw=5, alpha=.55, solid_capstyle="round")
        a1.plot([np.mean(v)], [yy], "o", color=c, ms=6)
        if hi - lo > .45:
            a1.text(lo - .25, yy, f"{lo:.1f}", ha="right", va="center", fontsize=7.2, color="#555")
            a1.text(hi + .25, yy, f"{hi:.1f}", ha="left", va="center", fontsize=7.2, color="#555")
        a1.text(-6.2, yy + .26, f"sd {v.std():.2f}", ha="left", va="center", fontsize=7.4, color="#777")
    a1.set_yticks([0, 1, 2])
    a1.set_yticklabels(["Revised\nmodel", "Original\nmodel", "Actual\nreturns"], fontsize=8.4)
    a1.set_ylim(-.55, 2.75)
    a1.set_xlim(-6.5, 10)
    a1.set_xlabel("Percentage points per session", fontsize=8.6)
    a1.set_title("Forecasts are far narrower than returns", fontsize=9.2, loc="left")
    a1.text(-6.2, 2.62, "bars span the 5th to 95th percentile", fontsize=7.0, color="#8a8f93")
    a1.tick_params(axis="x", labelsize=8)
    for side in ("top", "right", "left"):
        a1.spines[side].set_visible(False)

    a2.scatter(y, fc["forecast_basic"], s=9, color=ORANGE, alpha=.55, linewidth=0)
    b = np.polyfit(y, fc["forecast_basic"], 1)
    xs = np.array([-5, 9])
    a2.plot(xs, np.polyval(b, xs), color="#3a3a3a", lw=1.1)
    a2.axhline(0, color="#c7c7c7", lw=.8)
    a2.set_xlabel("Actual next-session return (pp)", fontsize=8.6)
    a2.set_ylabel("Original model's forecast (pp)", fontsize=8.6)
    a2.set_title("Its forecasts barely track outcomes (r = 0.05)", fontsize=9.2, loc="left")
    a2.tick_params(labelsize=8)
    for side in ("top", "right"):
        a2.spines[side].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIGS / "figure_behaviour.png", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    figure_timeline()
    figure_model()
    figure_behaviour()
    figure1()
    figure2()
    print("figures written:", sorted(p.name for p in FIGS.glob("*.png")))
