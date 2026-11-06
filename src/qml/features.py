"""Step 2 — Features: what the model knows about each stock on each day.

Test:  pytest tests/test_features.py
"""

from __future__ import annotations

import pandas as pd


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add the five features in config.FEATURES. Every value on day t may use data
    up to and including day t's close — never anything later (look-ahead bias).

    Each feature is computed per stock (groupby "code"), over the stock's own rows:
      * mom_20    — momentum: close[t] / close[t-20] - 1            (20-row pct_change)
      * rev_5     — short-term reversal: MINUS the 5-row return:  -(close[t]/close[t-5] - 1)
                    (minus, so that "higher = expected to go up" for every feature)
      * vol_20    — volatility: std of the last 20 daily close-to-close returns
      * turn_20   — mean of the last 20 days' turnover (% of shares traded)
      * amihud_20 — illiquidity: mean over 20 days of |daily return| / amount, times 1e9
                    (how much the price moves per unit of money traded)
    The first rows of each stock, without enough history, are NaN (tested).

    Return a copy sorted by code, date with a fresh index.
    Hints:
      * g = df.groupby("code"); g["close"].pct_change(20) works per stock.
      * Rolling per stock: series.groupby(df["code"]).transform(lambda s: s.rolling(20).std())
    """
    raise NotImplementedError("Step 2: implement compute_features")


def rank_by_date(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Replace each column in `cols` by its percentile rank WITHIN EACH DATE (0..1].

    Why: a model should learn "this stock's momentum is high compared with other stocks
    TODAY", not raw levels that drift with the whole market. NaN stays NaN.
    Hint: df.groupby("date")[cols].rank(pct=True). Don't modify the input.
    """
    raise NotImplementedError("Step 2: implement rank_by_date")
