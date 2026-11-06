"""Step 3 — Signal quality: the Information Coefficient (IC).

Test:  pytest tests/test_metrics.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from qml.config import MIN_STOCKS_PER_DATE


def rank_ic_by_date(df: pd.DataFrame, signal: str, label: str = "fwd_ret",
                    min_stocks: int = MIN_STOCKS_PER_DATE) -> pd.Series:
    """For every date, the Spearman (rank) correlation between `signal` and `label`
    across stocks. Returns a Series indexed by date, sorted, named "rank_ic".

    Requirements (tested):
      * Drop rows where signal or label is NaN first.
      * Skip dates with fewer than `min_stocks` remaining stocks (too few to rank).
      * Spearman correlation = Pearson correlation of the ranks:
        grp[signal].rank().corr(grp[label].rank())
    """
    raise NotImplementedError("Step 3: implement rank_ic_by_date")


def ic_summary(ic: pd.Series) -> dict:
    """Summarise a daily IC series. Return a dict of plain Python floats/ints:
      mean, std (ddof=1), icir = mean / std, t_stat = mean / std * sqrt(n),
      hit_rate = share of dates with IC > 0, n_dates = number of non-NaN dates.
    If std is 0, icir and t_stat are 0.0. Cast numpy numbers with float() (tested).
    """
    raise NotImplementedError("Step 3: implement ic_summary")
