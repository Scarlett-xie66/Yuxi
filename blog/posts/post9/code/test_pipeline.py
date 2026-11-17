"""Checks on the saved results, independent of the code that produced them.

Run from the project root:  python3 -m unittest discover -s code -p "test_*.py" -v

The point is to catch the two mistakes this kind of pipeline makes silently:
a forecast that uses information from the session it is predicting, and a
number in the article that the saved outputs no longer support.
"""

import hashlib
import json
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "SP500.csv"
RES = ROOT / "result" / "tables"

CFG = json.loads((RES / "experiment.json").read_text())
FC = pd.read_csv(ROOT / "data" / "processed" / "forecasts.csv", parse_dates=["date"]).set_index("date")
TM = pd.read_csv(RES / "test_metrics.csv").set_index("model")
CS = pd.read_csv(RES / "cost_sensitivity.csv")
DIAG = json.loads((RES / "diagnostics.json").read_text())

PANEL = pd.read_csv(ROOT / "data" / "processed" / "panel.csv", parse_dates=["date"]).set_index("date")

PRICES = (pd.read_csv(RAW, parse_dates=["observation_date"])
          .rename(columns={"observation_date": "date", "SP500": "close"})
          .set_index("date")["close"].astype(float).dropna())


def target_series():
    """Return from close t+1 to close t+2, in percentage points, indexed by t."""
    c = PRICES
    return ((c.shift(-2) / c.shift(-1) - 1) * 100).dropna()


class TestNoLookahead(unittest.TestCase):

    def test_target_definition_matches_prices(self):
        tgt = target_series()
        check = FC.index[:20].append(FC.index[-20:])
        for d in check:
            self.assertAlmostEqual(FC.loc[d, "realized_return_pp"], tgt.loc[d], places=6,
                                   msg=f"target mismatch on {d.date()}")
        self.assertAlmostEqual(float(PANEL["y"].mean()), float(tgt.reindex(PANEL.index).mean()), places=9)

    def test_benchmark_uses_only_pre_test_data(self):
        pre = PANEL.loc[: pd.Timestamp(CFG["validation"][1]), "y"]
        self.assertAlmostEqual(CFG["benchmark_constant_pp"], float(pre.mean()), places=9)

    def test_lag_features_use_only_past_prices(self):
        """lag1 is the return realised on t itself (known at that close); lag2 is
        yesterday's, and so on. Nothing later than t may enter a forecast."""
        ret = (PRICES / PRICES.shift(1) - 1) * 100
        for k in (1, 3, 5):
            d = PANEL.index[:5].append(PANEL.index[-5:])
            for t in d:
                src = PRICES.index[PRICES.index.get_loc(t) - (k - 1)]
                self.assertAlmostEqual(PANEL.loc[t, f"lag{k}"], ret.loc[src], places=9,
                                       msg=f"lag{k} wrong on {t.date()}")

        self.assertEqual(set(FC["forecast_benchmark"].round(9)), {round(CFG["benchmark_constant_pp"], 9)})

    def test_target_is_not_the_same_session_return(self):
        """A one-session-ahead target would match the t -> t+1 return; it must not."""
        one_step = ((PRICES.shift(-1) / PRICES - 1) * 100).reindex(FC.index)
        overlap = float(np.mean(np.isclose(FC["realized_return_pp"], one_step)))
        self.assertLess(overlap, 0.05)


class TestSavedOutputs(unittest.TestCase):

    def test_split_sizes(self):
        self.assertEqual(CFG["train_obs"], 1239)
        self.assertEqual(CFG["validation_obs"], 501)
        self.assertEqual(CFG["test_obs"], 502)
        self.assertEqual(len(FC), 502)
        self.assertEqual(FC.index[0].year, 2024)

    def test_metrics_recompute_from_forecasts(self):
        y = FC["realized_return_pp"].values
        for model, col in [("Historical mean", "forecast_benchmark"),
                           ("Five-session mean", "forecast_naive"),
                           ("Basic boosting", "forecast_basic"),
                           ("Regularized boosting", "forecast_regularized")]:
            pred = FC[col].values
            rmse = float(np.sqrt(np.mean((y - pred) ** 2)))
            self.assertAlmostEqual(TM.loc[model, "rmse"], rmse, places=9)
            acc = float(np.mean(np.sign(pred) == np.sign(y)) * 100)
            self.assertAlmostEqual(TM.loc[model, "direction_accuracy_pct"], acc, places=9)

    def test_costs_always_hurt(self):
        for strategy in CS["strategy"].unique():
            r = CS[CS.strategy == strategy].set_index("cost_per_trade")["total_return_pct"]
            self.assertGreater(r[0.0], r[0.0005])
            self.assertGreater(r[0.0005], r[0.001])

    def test_cash_days_match_diagnostics(self):
        cd = pd.read_csv(RES / "cash_days.csv", parse_dates=["date"])
        self.assertEqual(len(cd), DIAG["cash_sessions"])
        self.assertTrue(DIAG["trough_in_cash"])
        self.assertIn(pd.Timestamp(DIAG["trough_date"]), set(cd["date"]))

    def test_source_checksum(self):
        sha = hashlib.sha256(RAW.read_bytes()).hexdigest()
        self.assertEqual(CFG["source_sha256"], sha)

    def test_no_missing_values_in_forecasts(self):
        self.assertFalse(FC.isna().any().any())


class TestInference(unittest.TestCase):

    def test_bootstrap_is_deterministic(self):
        sys.path.insert(0, str(ROOT / "code"))
        from evaluate_investment import boot_ci  # noqa: E402
        rng_vals = np.random.default_rng(0).normal(size=300)
        self.assertEqual(boot_ci(rng_vals, seed=7), boot_ci(rng_vals, seed=7))
        self.assertNotEqual(boot_ci(rng_vals, seed=7), boot_ci(rng_vals, seed=8))

    def test_intervals_contain_their_point_estimates(self):
        inf = pd.read_csv(RES / "inference.csv")
        rows = inf[inf["comparison"].str.contains("historical mean")]
        for r in rows.itertuples():
            self.assertLess(r.boot_lo_pct, r.mse_gap_pct)
            self.assertGreater(r.boot_hi_pct, r.mse_gap_pct)


if __name__ == "__main__":
    unittest.main(verbosity=2)
