"""Collect every number the article quotes into result/tables/numbers.csv.

The Quarto article (index.qmd) prints nothing typed by hand: each inline value
in the text is ``r v$name``, and v is this file. Formatting lives here so that
the article text stays free of decimals, signs and rounding rules.
"""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "result" / "tables"
PROCESSED = ROOT / "data" / "processed"
OUT = RES / "numbers.csv"


def num(x, d=2, sign=False):
    txt = f"{x:+.{d}f}" if sign else f"{x:.{d}f}"
    return txt.replace("-", "\u2212")


def main():
    cfg = json.loads((RES / "experiment.json").read_text())
    diag = json.loads((RES / "diagnostics.json").read_text())
    tm = pd.read_csv(RES / "test_metrics.csv").set_index("model")
    inf = pd.read_csv(RES / "inference.csv")
    inv = pd.read_csv(RES / "investment_metrics.csv").set_index("strategy")
    cs = pd.read_csv(RES / "cost_sensitivity.csv")
    fb = pd.read_csv(RES / "forecast_behaviour.csv").set_index("model")
    basicfb, regfb, realfb = fb.loc["Basic boosting"], fb.loc["Regularized boosting"], fb.loc["Realized returns"]
    val_grid = pd.read_csv(RES / "validation_grid.csv")

    base = inf[inf["comparison"].str.startswith("Basic")].iloc[0]
    regb = inf[inf["comparison"].str.startswith("Regularized boosting")].iloc[0]
    retgap = inf[inf["comparison"].str.contains("continuous")].iloc[0]

    bench, naive, basic, reg = (tm.loc["Historical mean"], tm.loc["Five-session mean"],
                               tm.loc["Basic boosting"], tm.loc["Regularized boosting"])
    nav = inf[inf["comparison"].str.startswith("Five-session")].iloc[0]
    cont, basi, regi = (inv.loc["Continuous index exposure"], inv.loc["Basic boosting"],
                        inv.loc["Regularized boosting"])

    def csrow(strategy):
        r = cs[cs.strategy == strategy].set_index("cost_per_trade")["total_return_pct"]
        return [num(r[0.0]), num(r[0.0005]), num(r[0.001])]

    v = {
        "bench_rmse": num(bench.rmse, 4), "basic_rmse": num(basic.rmse, 4), "reg_rmse": num(reg.rmse, 4),
        "bench_gap": num(bench.mse_relative_pct), "basic_gap": num(basic.mse_relative_pct),
        "reg_gap": num(reg.mse_relative_pct),
        "basic_lo": num(base.boot_lo_pct, 1, True), "basic_hi": num(base.boot_hi_pct, 1, True),
        "reg_lo": num(regb.boot_lo_pct, 1, True), "reg_hi": num(regb.boot_hi_pct, 1, True),
        "basic_dm_p": num(base.dm_p_value, 3), "reg_dm_p": num(regb.dm_p_value, 3),
        "bench_dir": num(bench.direction_accuracy_pct, 1), "basic_dir": num(basic.direction_accuracy_pct, 1),
        "reg_dir": num(reg.direction_accuracy_pct, 1),
        "naive_rmse": num(naive.rmse, 4), "naive_gap": num(naive.mse_relative_pct),
        "naive_lo": num(nav.boot_lo_pct, 1, True), "naive_hi": num(nav.boot_hi_pct, 1, True),
        "naive_dir": num(naive.direction_accuracy_pct, 1),
        "naive_dm_p": num(nav.dm_p_value, 3),
        "bench_mae": num(bench.mae, 3), "reg_mae": num(reg.mae, 3), "basic_mae": num(basic.mae, 3),
        "bench_pp": num(cfg["benchmark_constant_pp"], 3),
        "train_n": f'{cfg["train_obs"]:,}', "val_n": f'{cfg["validation_obs"]:,}', "test_n": f'{cfg["test_obs"]:,}',
        "cont_net": num(cont.total_return_pct), "basic_net": num(basi.total_return_pct),
        "reg_net": num(regi.total_return_pct),
        "cont_mdd": num(abs(cont.max_drawdown_pct)), "reg_mdd": num(abs(regi.max_drawdown_pct)),
        "basic_mdd": num(abs(basi.max_drawdown_pct)),
        "cont_vol": num(cont.annualized_volatility_pct), "reg_vol": num(regi.annualized_volatility_pct),
        "cont_sharpe": num(cont.sharpe_zero_cash), "reg_sharpe": num(regi.sharpe_zero_cash),
        "cont_trades": f"{int(cont.one_way_trades)}", "reg_trades": f"{int(regi.one_way_trades)}",
        "basic_trades": f"{int(basi.one_way_trades)}",
        "reg_invested": num(regi.invested_share_pct), "basic_invested": num(basi.invested_share_pct),
        "cash_n": f'{diag["cash_sessions"]}', "test_sessions": f'{diag["test_sessions"]}',
        "cash_ret": num(abs(diag["mean_return_cash_days_pp"]), 3), "invested_ret": num(diag["mean_return_invested_days_pp"], 3),
        "trough": diag["trough_date"], "peak": diag["max_drawdown_window"][0],
        "gap_before_selloff": num(abs(diag["drawdown_gap_before_selloff_pp"]), 1),
        "cash_apr": f'{diag["cash_sessions_april_2025"]}',
        "train_rmse": num(cfg["in_sample_rmse_pp"]["basic"], 2),
        "train_sd": num(cfg["in_sample_rmse_pp"]["target_sd"], 2),
        "gap_pp": num(abs(retgap.mse_gap_pct)), "gap_lo": num(retgap.boot_lo_pct, 1, True),
        "gap_hi": num(retgap.boot_hi_pct, 1, True),
        "cont_end": num(100 * (1 + cont.total_return_pct / 100)), "reg_end": num(100 * (1 + regi.total_return_pct / 100)),
        "basic_end": num(100 * (1 + basi.total_return_pct / 100)),
        "cont_gbr": num(cs[(cs.strategy == "Continuous index exposure") & (cs.cost_per_trade == 0)]["total_return_pct"].iloc[0]),
        "reg_gbr": num(cs[(cs.strategy == "Regularized boosting") & (cs.cost_per_trade == 0)]["total_return_pct"].iloc[0]),
        "cont_c0": csrow("Continuous index exposure")[0], "cont_c5": csrow("Continuous index exposure")[1],
        "cont_c10": csrow("Continuous index exposure")[2],
        "reg_c0": csrow("Regularized boosting")[0], "reg_c5": csrow("Regularized boosting")[1],
        "reg_c10": csrow("Regularized boosting")[2],
        "basic_c0": csrow("Basic boosting")[0], "basic_c5": csrow("Basic boosting")[1],
        "basic_c10": csrow("Basic boosting")[2],
        "basic_sd": num(basicfb.sd_forecast_pp, 2), "reg_sd": num(regfb.sd_forecast_pp, 2),
        "real_sd": num(realfb.sd_forecast_pp, 2),
        "basic_pos": num(basicfb.share_positive_pct, 1), "reg_pos": num(regfb.share_positive_pct, 1),
        "basic_fmin": num(basicfb.min_forecast_pp, 1, True), "basic_fmax": num(basicfb.max_forecast_pp, 1, True),
        "basic_corr": num(basicfb.corr_with_realized, 2),
        "basic_val_mse": num(cfg["basic_validation_mse"], 2),
        "reg_val_mse": num(val_grid.validation_mse.min(), 2),
        "val_gain": num(100 * (1 - val_grid.validation_mse.min() / cfg["basic_validation_mse"]), 1),
        "gain_pp": num(regi.total_return_pct - basi.total_return_pct, 1),
        "trades_cut": f'{int(basi.one_way_trades) - int(regi.one_way_trades)}',
        "sha": cfg["source_sha256"][:12], "sklearn": cfg["sklearn"],
    }

    df = pd.DataFrame({"key": list(v.keys()), "value": [str(x) for x in v.values()]})
    df.to_csv(OUT, index=False, encoding="utf-8")
    print(f"wrote {OUT} with {len(df)} values")


if __name__ == "__main__":
    main()
