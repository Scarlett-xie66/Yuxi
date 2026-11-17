"""Blog 9: predicting S&P 500 daily returns with gradient boosting.

Runs end to end from data/raw/SP500.csv and writes:
  data/processed/panel.csv        features and target by session
  data/processed/forecasts.csv    one row per test session
  result/tables/                  metrics, validation grid, behaviour, experiment.json
"""

import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import GradientBoostingRegressor

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "SP500.csv"
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "result" / "tables"
for d in (PROCESSED, TABLES):
    d.mkdir(parents=True, exist_ok=True)

START = "2017-01-01"
END = "2025-12-31"
VAL_START, VAL_END = "2022-01-01", "2023-12-31"
TEST_START = "2024-01-01"
SEED = 20261116

# Four regularized candidates; the first is the configuration the
# validation step is expected to select.
CANDIDATES = [
    dict(learning_rate=0.03, max_depth=1, min_samples_leaf=50),
    dict(learning_rate=0.05, max_depth=2, min_samples_leaf=30),
    dict(learning_rate=0.01, max_depth=2, min_samples_leaf=20),
    dict(learning_rate=0.10, max_depth=3, min_samples_leaf=10),
]
BASIC = dict(learning_rate=0.10, max_depth=3, min_samples_leaf=1)
FEATURES = ["lag1", "lag2", "lag3", "lag4", "lag5", "cum5", "cum20", "vol5", "vol20"]


def load_prices() -> pd.Series:
    raw = pd.read_csv(RAW)
    raw.columns = ["date", "sp500"]
    raw["sp500"] = pd.to_numeric(raw["sp500"], errors="coerce")
    raw = raw.dropna()
    raw["date"] = pd.to_datetime(raw["date"])
    # Keep two extra sessions past END so the last two targets exist.
    series = raw.set_index("date").sort_index()["sp500"]
    keep = series[(series.index >= START) & (series.index <= "2026-01-15")]
    return keep


def build_panel(series: pd.Series) -> pd.DataFrame:
    ret = series.pct_change() * 100  # percentage points
    panel = pd.DataFrame(index=series.index)
    for k in range(5):
        panel[f"lag{k + 1}"] = ret.shift(k)
    panel["cum5"] = ret.rolling(5).sum()
    panel["cum20"] = ret.rolling(20).sum()
    panel["vol5"] = ret.rolling(5).std()
    panel["vol20"] = ret.rolling(20).std()
    # Features are known after session t; target runs from t+1 close to t+2 close.
    panel["y"] = ret.shift(-2)
    panel["ret_next"] = ret.shift(-1)
    panel = panel.dropna(subset=FEATURES + ["y"])
    return panel[panel.index <= END]


def split(panel: pd.DataFrame):
    train = panel[panel.index <= "2021-12-31"]
    valid = panel[(panel.index >= VAL_START) & (panel.index <= VAL_END)]
    test = panel[panel.index >= TEST_START]
    return train, valid, test


def fit_basic(train, valid, test):
    model = GradientBoostingRegressor(n_estimators=100, random_state=SEED, **BASIC)
    # Refit on every eligible pre-test outcome before forecasting the test period.
    model.fit(pd.concat([train, valid])[FEATURES], pd.concat([train, valid])["y"])
    return model


def select_regularized(train, valid):
    rows, models = [], {}
    for i, cfg in enumerate(CANDIDATES):
        m = GradientBoostingRegressor(n_estimators=100, random_state=SEED, **cfg)
        m.fit(train[FEATURES], train["y"])
        mse = float(np.mean((valid["y"].values - m.predict(valid[FEATURES])) ** 2))
        rows.append({"candidate": i + 1, "learning_rate": cfg["learning_rate"],
                     "max_depth": cfg["max_depth"],
                     "min_samples_leaf": cfg["min_samples_leaf"],
                     "validation_mse": mse})
        models[i] = m
    grid = pd.DataFrame(rows)
    winner = int(grid.loc[grid["validation_mse"].idxmin(), "candidate"])
    return grid, winner


def metrics(y, pred, bench_const):
    e = y - pred
    e0 = y - bench_const
    mse, mse0 = float(np.mean(e ** 2)), float(np.mean(e0 ** 2))
    return {
        "rmse": float(np.sqrt(mse)),
        "rmse_benchmark": float(np.sqrt(mse0)),
        "mse_relative_pct": (mse / mse0 - 1) * 100,
        "mae": float(np.mean(np.abs(e))),
        "direction_accuracy_pct": float(np.mean(np.sign(pred) == np.sign(y)) * 100),
    }


def main():
    series = load_prices()
    panel = build_panel(series)
    panel.to_csv(PROCESSED / "panel.csv", index_label="date")
    train, valid, test = split(panel)
    # A no-model benchmark must use every pre-test observation, not just the
    # training block, or it would be handicapped by information we already have.
    bench_const = float(pd.concat([train, valid])["y"].mean())

    grid, winner = select_regularized(train, valid)
    mbasic = GradientBoostingRegressor(n_estimators=100, random_state=SEED, **BASIC).fit(train[FEATURES], train["y"])
    basic_val_mse = float(np.mean((valid["y"].values - mbasic.predict(valid[FEATURES])) ** 2))
    grid.to_csv(TABLES / "validation_grid.csv", index=False)
    winner_cfg = CANDIDATES[winner - 1]

    basic = fit_basic(train, valid, test)
    reg = GradientBoostingRegressor(n_estimators=100, random_state=SEED, **winner_cfg)
    reg.fit(pd.concat([train, valid])[FEATURES], pd.concat([train, valid])["y"])

    # In-sample fit on all pre-test rows, for the overfitting comparison in the article.
    ins = pd.concat([train, valid])
    in_sample = {}
    for tag, cfgm in [("basic", BASIC), ("regularized", winner_cfg)]:
        mi = GradientBoostingRegressor(n_estimators=100, random_state=SEED, **cfgm).fit(ins[FEATURES], ins["y"])
        in_sample[tag] = float(np.sqrt(np.mean((mi.predict(ins[FEATURES]) - ins["y"].values) ** 2)))
    in_sample["target_sd"] = float(ins["y"].std())

    y = test["y"].values
    pred_basic = basic.predict(test[FEATURES])
    pred_reg = reg.predict(test[FEATURES])
    # Naive rule: average of the five most recent *realised* targets at close t.
    # Row t-2 already resolves at close t, so the average lags two sessions.
    naive_series = panel["y"].shift(2).rolling(5).mean()
    pred_naive = naive_series.reindex(test.index).values

    rows = []
    for name, pred in [("Historical mean", np.full_like(y, bench_const)),
                       ("Five-session mean", pred_naive),
                       ("Basic boosting", pred_basic),
                       ("Regularized boosting", pred_reg)]:
        m = metrics(y, pred, bench_const)
        rows.append({"model": name, **m})
    tm = pd.DataFrame(rows)
    tm.to_csv(TABLES / "test_metrics.csv", index=False)
    print(tm.to_string(index=False))

    behave = []
    for name, pred in [("Basic boosting", pred_basic), ("Regularized boosting", pred_reg)]:
        behave.append({"model": name, "mean_forecast_pp": float(np.mean(pred)),
                       "sd_forecast_pp": float(np.std(pred)),
                       "share_positive_pct": float(np.mean(pred > 0) * 100),
                       "min_forecast_pp": float(np.min(pred)), "max_forecast_pp": float(np.max(pred)),
                       "corr_with_realized": float(np.corrcoef(pred, y)[0, 1])})
    behave.append({"model": "Realized returns", "mean_forecast_pp": float(np.mean(y)),
                   "sd_forecast_pp": float(np.std(y)), "share_positive_pct": float(np.mean(y > 0) * 100),
                   "min_forecast_pp": float(np.min(y)), "max_forecast_pp": float(np.max(y)),
                   "corr_with_realized": float("nan")})
    pd.DataFrame(behave).to_csv(TABLES / "forecast_behaviour.csv", index=False)

    fc = pd.DataFrame({
        "date": test.index, "realized_return_pp": y,
        "forecast_benchmark": bench_const,
        "forecast_basic": pred_basic,
        "forecast_naive": pred_naive,
        "forecast_regularized": pred_reg,
    })
    fc.to_csv(PROCESSED / "forecasts.csv", index=False)

    cfg = {
        "start": START, "end": END,
        "train_obs": int(len(train)), "validation_obs": int(len(valid)), "test_obs": int(len(test)),
        "train_end": "2021-12-31", "validation": [VAL_START, VAL_END], "test_start": TEST_START,
        "features": FEATURES,
        "target": "close(t+1) -> close(t+2) return, percentage points",
        "basic_config": BASIC,
        "candidate_configs": CANDIDATES,
        "selected_candidate": winner,
        "selected_config": winner_cfg,
        "benchmark_constant_pp": bench_const,
        "basic_validation_mse": basic_val_mse,
        "in_sample_rmse_pp": in_sample,
        "seed": SEED,
        "sklearn": sklearn.__version__,
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "python": platform.python_version(),
        "source_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest(),
    }
    (TABLES / "experiment.json").write_text(json.dumps(cfg, indent=2))
    print(json.dumps({k: cfg[k] for k in
                      ["train_obs", "validation_obs", "test_obs", "selected_candidate",
                       "benchmark_constant_pp", "source_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
