"""Investment evaluation, inference and diagnostics for the Blog 9 revision.

Reads data/processed/forecasts.csv and writes to result/tables/:
  investment_metrics.csv, cost_sensitivity.csv, inference.csv, cash_days.csv,
  diagnostics.json
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
RES = ROOT / "result" / "tables"
BPS = [0.0, 0.0005, 0.0010]
MAIN_BPS = 0.0005
BOOT = 2000
SEED = 20261116
TRADING_DAYS = 252


def simulate(returns: np.ndarray, position: np.ndarray, cost: float):
    """position[i] applies to returns[i]; a change in position is a trade."""
    r = np.asarray(returns, dtype=float) / 100.0    # percentage points -> decimal
    held = np.where(position != 0, 1.0, 0.0)
    prev = np.concatenate([[0.0], held[:-1]])          # held before session i
    entries = (held != prev).astype(float)             # entry and every flip
    gross = 1.0 + held * r
    net = gross * (1.0 - cost * entries)
    wealth = np.cumprod(net)
    wealth_final = wealth[-1] * (1.0 - cost)           # final liquidation
    drawdown = wealth / np.maximum.accumulate(np.concatenate([[1.0], wealth]))[1:] - 1.0
    daily = net - 1.0
    ann_vol = float(np.std(daily, ddof=1) * np.sqrt(TRADING_DAYS) * 100)
    ann_mean = float(np.mean(daily) * TRADING_DAYS * 100)
    sharpe = ann_mean / ann_vol if ann_vol > 0 else np.nan
    return {
        "total_return_pct": float((wealth_final - 1.0) * 100),
        "max_drawdown_pct": float(drawdown.min() * 100),
        "annualized_volatility_pct": ann_vol,
        "sharpe_zero_cash": float(sharpe),
        "one_way_trades": int(entries.sum()) + 1,
        "invested_share_pct": float(held.mean() * 100),
        "wealth": wealth,
    }


def dm_test(e1, e2, lag=5):
    """Diebold-Mariano on squared-error loss: positive stat favours model 1."""
    d = e2 ** 2 - e1 ** 2
    n = len(d)
    dbar = d.mean()
    dc = d - dbar
    var = float(np.mean(dc ** 2))
    for k in range(1, lag + 1):
        w = 1 - k / (lag + 1)
        var += 2 * w * float(np.mean(dc[k:] * dc[:-k]))
    stat = dbar / np.sqrt(var / n)
    p = float(2 * (1 - stats.norm.cdf(abs(stat))))
    return float(stat), float(dbar), n, p


def boot_ci(values, stat=np.mean, reps=BOOT, seed=SEED, alpha=0.05):
    rng = np.random.default_rng(seed)
    n = len(values)
    draws = np.array([stat(values[rng.integers(0, n, n)]) for _ in range(reps)])
    return float(np.quantile(draws, alpha / 2)), float(np.quantile(draws, 1 - alpha / 2))


def main():
    fc = pd.read_csv(PROCESSED / "forecasts.csv", parse_dates=["date"])
    y = fc["realized_return_pp"].values
    bench = fc["forecast_benchmark"].values
    basic = fc["forecast_basic"].values
    reg = fc["forecast_regularized"].values

    names = {
        "Continuous index exposure": np.ones_like(y),
        "Basic boosting": (basic > 0).astype(float),
        "Regularized boosting": (reg > 0).astype(float),
    }

    rows, wealth = [], {}
    for name, pos in names.items():
        r = simulate(y, pos, MAIN_BPS)
        wealth[name] = r.pop("wealth")
        rows.append({"strategy": name, **r})
    inv = pd.DataFrame(rows)
    inv.to_csv(RES / "investment_metrics.csv", index=False)
    print(inv.to_string(index=False))

    cost_rows = []
    for name, pos in names.items():
        for c in BPS:
            r = simulate(y, pos, c)
            cost_rows.append({"strategy": name, "cost_per_trade": c,
                              "total_return_pct": r["total_return_pct"],
                              "max_drawdown_pct": r["max_drawdown_pct"]})
    cs = pd.DataFrame(cost_rows)
    cs.to_csv(RES / "cost_sensitivity.csv", index=False)
    print(cs.to_string(index=False))

    # Inference on the predictive gap and on the return gap.
    e0, e1, e2 = y - bench, y - basic, y - reg
    e3 = y - fc["forecast_naive"].values
    mse0 = float(np.mean(e0 ** 2))
    inf = []
    for label, e in [("Basic boosting vs historical mean", e1),
                     ("Regularized boosting vs historical mean", e2),
                     ("Five-session mean vs historical mean", e3)]:
        stat, dbar, n, p = dm_test(e, e0)
        # per-session loss differential, scaled by the benchmark's mean squared error
        d_rel = (e ** 2 - e0 ** 2) / mse0 * 100
        lo, hi = boot_ci(d_rel)
        inf.append({"comparison": label, "dm_stat": stat, "dm_p_value": p, "dm_lag": 5,
                    "mse_diff_pp2": dbar, "mse_gap_pct": float(np.mean(e ** 2 - e0 ** 2) / mse0 * 100),
                    "boot_lo_pct": lo, "boot_hi_pct": hi, "n": n})
    ret_gap = wealth["Regularized boosting"] - wealth["Continuous index exposure"]
    diff = np.diff(np.concatenate([[0.0], ret_gap]))
    lo, hi = boot_ci(diff, stat=lambda v: v.sum() * 100)
    ci = {"comparison": "Regularized vs continuous (two-year net return, pp)",
          "dm_stat": np.nan, "dm_p_value": np.nan, "dm_lag": np.nan, "mse_diff_pp2": np.nan,
          "mse_gap_pct": float((wealth['Regularized boosting'][-1] -
                                wealth['Continuous index exposure'][-1]) * 100),
          "boot_lo_pct": lo, "boot_hi_pct": hi, "n": len(y)}
    inf.append(ci)
    infdf = pd.DataFrame(inf)
    infdf.to_csv(RES / "inference.csv", index=False)
    print(infdf.to_string(index=False))

    # Which sessions did the timing rule skip, and what happened on them?
    pos = (reg > 0).astype(float)
    cash_idx = np.where(pos == 0)[0]
    cd = fc.iloc[cash_idx][["date", "realized_return_pp", "forecast_regularized"]].copy()
    cd["mean_all_days_pp"] = y.mean()
    cd["mean_cash_day_pp"] = y[cash_idx].mean() if len(cash_idx) else np.nan
    cd["mean_invested_day_pp"] = y[pos == 1].mean()
    cd.to_csv(RES / "cash_days.csv", index=False)
    print(f"cash sessions: {len(cash_idx)} of {len(y)}; "
          f"mean return there {cd['mean_cash_day_pp'].iloc[0]:.3f} pp vs "
          f"{cd['mean_invested_day_pp'].iloc[0]:.3f} pp invested")

    wc = wealth["Continuous index exposure"]
    dd_end = int(np.argmin(wc / np.maximum.accumulate(np.concatenate([[1.0], wc]))[1:] - 1))
    wr = wealth["Regularized boosting"]
    dds = {
        "index": wc / np.maximum.accumulate(np.concatenate([[1.0], wc]))[1:] - 1,
        "reg": wr / np.maximum.accumulate(np.concatenate([[1.0], wr]))[1:] - 1,
    }
    dates = pd.Series(fc["date"].values, index=fc.index)
    pre_idx = int(np.where(dates <= pd.Timestamp("2025-03-31"))[0][-1])
    gap_pre = float((dds["reg"][pre_idx] - dds["index"][pre_idx]) * 100)
    gap_end = float((dds["reg"][-1] - dds["index"][-1]) * 100)
    april_cash = int(((fc["date"] >= "2025-04-01") & (fc["date"] <= "2025-04-30") & (pos == 0)).sum())
    diag = {
        "drawdown_gap_before_selloff_pp": gap_pre,
        "drawdown_gap_at_end_pp": gap_end,
        "cash_sessions_april_2025": april_cash,
        "trough_date": str(fc["date"].iloc[dd_end].date()),
        "trough_in_cash": bool(pos[dd_end] == 0),
        "cash_sessions": int(len(cash_idx)),
        "test_sessions": int(len(y)),
        "mean_return_cash_days_pp": float(y[cash_idx].mean()) if len(cash_idx) else float("nan"),
        "mean_return_invested_days_pp": float(y[pos == 1].mean()),
        "max_drawdown_window": [str(fc["date"].iloc[int(np.argmax(wc[:dd_end + 1]))].date()),
                                str(fc["date"].iloc[dd_end].date())],
    }
    (RES / "diagnostics.json").write_text(json.dumps(diag, indent=2))
    print(json.dumps(diag, indent=2))


if __name__ == "__main__":
    main()
