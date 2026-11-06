"""Step 1 — Clean the raw panel and build the label (the future return we predict).

Test:  pytest tests/test_dataset.py
"""

from __future__ import annotations

import pandas as pd


def clean_panel(df: pd.DataFrame) -> pd.DataFrame:
    """Return a clean copy of the raw panel.

    Requirements (tested):
      * `date` converted to datetime (pd.to_datetime).
      * `code` as a 6-character string, zero-padded: 1 -> "000001".
        (CSV readers turn "000001" into the number 1 unless told otherwise.)
      * Drop rows with a missing open, close or volume.
      * Drop rows with volume <= 0, close <= 0 or open <= 0 (no real trading happened).
      * Drop duplicate (code, date) rows, keeping the last one.
      * Sort by code, then date, and reset the index to 0..n-1.
    Never modify the input DataFrame: start with df.copy().
    """
    raise NotImplementedError("Step 1: implement clean_panel")


def add_forward_return(df: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Add `fwd_ret`: the return we try to predict, for each stock and day.

    Timing (this is the most important design decision of the project — GUIDE.md, Step 1):
      the signal is computed after the CLOSE of day t, so the earliest we can trade is
      the OPEN of day t+1. We hold for `horizon` trading days and sell at the open of
      day t+1+horizon:

          fwd_ret[t] = open[t+1+horizon] / open[t+1] - 1

    Requirements (tested):
      * Computed separately per stock (groupby "code"): a return must never use
        another stock's prices.
      * "Day t+1" means the stock's NEXT ROW, i.e. its next trading day.
      * Rows without enough future data get NaN — never fill it.
      * Return a copy sorted by code, date with a fresh 0..n-1 index.
    Hint: groupby("code")["open"].shift(-k) gives the open k rows ahead in the same stock.
    """
    raise NotImplementedError("Step 1: implement add_forward_return")
