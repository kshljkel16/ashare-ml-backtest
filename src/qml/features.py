"""Step 2 — Features: what the model knows about each stock on each day.

Test:  pytest tests/test_features.py
"""

from __future__ import annotations

import pandas as pd


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.sort_values(["code", "date"]).copy()
    g = out.groupby("code", group_keys=False)
    daily_ret = g["close"].pct_change()                        # each day vs the previous day, per stock

    out["mom_20"] = g["close"].pct_change(20)                 # blank 1: 20-day momentum
    out["rev_5"] = -g["close"].pct_change(5)                 # blank 2: what sign? (read the docstring)
    out["vol_20"] = daily_ret.groupby(out["code"]).transform(
        lambda s: s.rolling(20).std())                         # blank 3: volatility = which statistic?
    out["turn_20"] = g["turnover"].transform(lambda s: s.rolling(20).mean())
    illiq = daily_ret.abs() / out["amount"] * 1e9              # |return| per unit of money traded
    out["amihud_20"] = illiq.groupby(out["code"]).transform(
        lambda s: s.rolling(20).mean())                       # blank 4: same window as the others
    return out.reset_index(drop=True)


def rank_by_date(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    out[cols] = out.groupby("date")[cols].rank(pct=True)          # blank 5: rank among stocks on the SAME ...?
    return out