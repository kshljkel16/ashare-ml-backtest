"""Synthetic A-share-like daily data with a KNOWN, planted signal.

Why this exists:
  1. Tests run offline, fast and deterministically — no downloads.
  2. It is a "known answer" check for your whole pipeline. The data contains two
     planted effects, so a correct pipeline MUST find them:
       * momentum  — each stock has a slowly drifting expected return, so stocks that
                     went up over ~20 days tend to keep going up a little;
       * reversal  — part of each day's noise is reversed the next day, so very
                     recent winners tend to give a little back.
     If your features, labels or backtest cannot find these, the pipeline is broken.
     Quant teams use planted-signal tests exactly for this reason.

The output has the same columns as the real data from `qml.data`:
    date, code, open, high, low, close, volume, amount, turnover

Usage:
    python -m qml.synthetic            # writes data/synthetic.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def make_panel(n_stocks: int = 120, n_days: int = 900, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2019-01-02", periods=n_days)

    market = rng.normal(0.0003, 0.012, n_days)                  # common daily market move
    rows = []
    for k in range(n_stocks):
        code = f"{600000 + k:06d}"
        beta = rng.uniform(0.7, 1.3)
        noise_sd = rng.uniform(0.015, 0.03)

        # Planted momentum: a persistent drift (AR(1), phi = 0.99)
        drift = np.zeros(n_days)
        for t in range(1, n_days):
            drift[t] = 0.99 * drift[t - 1] + rng.normal(0, 0.00025)

        # Planted reversal: 30% of yesterday's noise is taken back today
        eps = rng.normal(0, noise_sd, n_days)
        ret = drift + beta * market + eps
        ret[1:] -= 0.3 * eps[:-1]
        ret = np.clip(ret, -0.095, 0.095)                       # A-share daily limit is ±10%

        close = 10 * rng.uniform(0.5, 5) * np.exp(np.cumsum(ret))
        open_ = np.empty(n_days)
        open_[0] = close[0]
        open_[1:] = close[:-1] * np.exp(rng.normal(0, 0.004, n_days - 1))   # overnight gap
        high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, 0.006, n_days)))
        low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, 0.006, n_days)))
        turnover = np.exp(rng.normal(np.log(rng.uniform(0.5, 3.0)), 0.4, n_days))   # % of shares
        volume = np.round(turnover * 1e6 * rng.uniform(1, 5)).astype(np.int64)
        amount = volume * close

        df = pd.DataFrame({"date": dates, "code": code, "open": open_, "high": high,
                           "low": low, "close": close, "volume": volume,
                           "amount": amount, "turnover": turnover})

        # Some stocks list later (IPO): drop their first rows
        if rng.random() < 0.1:
            df = df.iloc[rng.integers(100, 300):]
        # Suspensions: real data simply has no row on a suspended day
        keep = rng.random(len(df)) > 0.01
        rows.append(df[keep])

    panel = pd.concat(rows, ignore_index=True)
    return panel.sort_values(["date", "code"]).reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("data/synthetic.csv"))
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df = make_panel(seed=args.seed)
    df.to_csv(args.out, index=False)
    print(f"wrote {len(df):,} rows, {df.code.nunique()} stocks, "
          f"{df.date.nunique()} days -> {args.out}")


if __name__ == "__main__":
    main()
