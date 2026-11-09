"""Step 3 — Signal quality: the Information Coefficient (IC).

Test:  pytest tests/test_metrics.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from qml.config import MIN_STOCKS_PER_DATE


def rank_ic_by_date(df: pd.DataFrame, signal: str, label: str = "fwd_ret",
                    min_stocks: int = MIN_STOCKS_PER_DATE) -> pd.Series:
    d = df[["date", signal, label]].dropna()            # only rows with both values
    out = {}
    for date, grp in d.groupby("date"):                    # blank 1: one IC per ...?
        if len(grp) < min_stocks:                              # blank 2: too few stocks to rank -> skip
            continue
        out[date] = grp[signal].rank().corr(grp[label].rank())   # blank 3: Spearman = correlation of RANKS
    return pd.Series(out, name="rank_ic", dtype=float).sort_index()


def ic_summary(ic: pd.Series) -> dict:
    ic = ic.dropna()
    n = len(ic)
    mean, std = float(ic.mean()), float(ic.std(ddof=1))
    return {
        "mean": mean,
        "std": std,
        "icir": mean / std if std > 0 else 0.0,
        "t_stat": float(mean / std * np.sqrt(n)) if std > 0 else 0.0,   # blank 4
        "hit_rate": float((ic > 0).mean()),                             # blank 5: share of positive days
        "n_dates": n,
    }
