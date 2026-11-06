"""Step 1 — Clean the raw panel and build the label (the future return we predict).

Test:  pytest tests/test_dataset.py
"""

from __future__ import annotations

import pandas as pd


def clean_panel(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()                                        # never modify the caller's data
    out["date"] = pd.to_datetime(out["date"])
    out["code"] = out["code"].astype(str).str.zfill(6)   # blank 1: how many digits is a code?
    out = out.dropna(subset=["open", "close", "volume"])
    out = out[(out["volume"] > 0) & (out["close"] > 0) & (out["open"] > 0)]
    out = out.drop_duplicates(subset=["code", "date"], keep="last")   # blank 2: the docstring says which
    return out.sort_values(["code", "date"]).reset_index(drop=True)


def add_forward_return(df: pd.DataFrame, horizon: int) -> pd.DataFrame:
    out = df.sort_values(["code", "date"]).copy()
    g = out.groupby("code")["open"]
    entry = g.shift(- 1)                    # blank 3: the open of the NEXT row (day t+1)
    exit_ = g.shift(-(1+horizon))                    # blank 4: the open of day t+1+horizon
    out["fwd_ret"] = exit_ / entry - 1
    return out.reset_index(drop=True)

