"""Step 6 — Turn labelled announcements into events, and measure what happens after them."""

from __future__ import annotations

import numpy as np
import pandas as pd


def align_to_trading_days(ann: pd.DataFrame, trading_days) -> pd.DataFrame:
    days = np.array(sorted(pd.unique(pd.to_datetime(pd.Series(trading_days)))))
    out = ann.copy()
    out["date"] = pd.to_datetime(out["date"])
    idx = np.searchsorted(days, out["date"].values, side="right") - 1   # last trading day <= date
    keep = idx >= 0                                                      # -1 = before our data starts
    out = out[keep].copy()
    out["signal_date"] = days[idx[keep]]
    return out.reset_index(drop=True)


def daily_event_scores(labeled: pd.DataFrame) -> pd.DataFrame:
    d = labeled.dropna(subset=["sentiment"])                             # unparsed LLM answers out
    out = (d.groupby(["code", "signal_date"])
             .agg(n_ann=("sentiment", "size"), score=("sentiment", "sum"))
             .reset_index())
    out["group"] = np.select([out["score"] > 0, out["score"] < 0], ["positive", "negative"], "neutral")
    return out


def abnormal_returns(panel: pd.DataFrame, horizons: list[int]) -> pd.DataFrame:
    out = panel.sort_values(["code", "date"]).copy()
    g = out.groupby("code")["open"]
    for h in horizons:
        fwd = g.shift(-(1 + h)) / g.shift(-1) - 1                        # next open -> open h days later
        out[f"abn_{h}"] = fwd - fwd.groupby(out["date"]).transform("mean")   # minus that day's average
    return out.reset_index(drop=True)


def event_study(abn: pd.DataFrame, events: pd.DataFrame, horizons: list[int]) -> pd.DataFrame:
    ev = events[["code", "signal_date", "group"]].rename(columns={"signal_date": "date"})
    d = abn.merge(ev, on=["code", "date"], how="left")
    d["group"] = d["group"].fillna("no_news")                            # days without announcements
    rows = []
    for grp, sub in d.groupby("group"):
        for h in horizons:
            x = sub[f"abn_{h}"].dropna()
            n = len(x)
            sd = x.std(ddof=1) if n > 1 else 0.0
            rows.append({"group": grp, "horizon": h, "n": n, "mean": float(x.mean()) if n else 0.0,
                         "t_stat": float(x.mean() / sd * np.sqrt(n)) if n > 1 and sd > 0 else 0.0})
    return pd.DataFrame(rows)