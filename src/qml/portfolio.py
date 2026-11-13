"""Step 5 — From signal to portfolio: quintiles, turnover, costs, Sharpe, drawdown.

Test:  pytest tests/test_portfolio.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from qml.config import N_QUANTILES, REBALANCE_EVERY


def rebalance_dates(dates, every: int = REBALANCE_EVERY) -> list:
    u = sorted(pd.unique(pd.to_datetime(pd.Series(dates))))
    return u[::every]                                   # blank 1: take every ___-th day


def quantile_returns(df, signal, label="fwd_ret", n_q=N_QUANTILES, every=REBALANCE_EVERY):
    d = df[["date", "code", signal, label]].dropna()
    d = d[d["date"].isin(rebalance_dates(d["date"], every))].copy()
    d["q"] = d.groupby("date")[signal].transform(
        lambda s: pd.qcut(s.rank(method="first"), n_q, labels=False) + 1)
    out = d.groupby(["date", "q"])[label].mean().unstack("q")    # blank 2: average WHAT per group?
    out.columns = [f"Q{int(c)}" for c in out.columns]
    return out.sort_index()


def top_quantile_turnover(df, signal, n_q=N_QUANTILES, every=REBALANCE_EVERY):
    d = df[["date", "code", signal]].dropna()
    d = d[d["date"].isin(rebalance_dates(d["date"], every))].copy()
    d["q"] = d.groupby("date")[signal].transform(
        lambda s: pd.qcut(s.rank(method="first"), n_q, labels=False) + 1)
    held = d[d["q"] == n_q].groupby("date")["code"].apply(set).sort_index()   # blank 3: the TOP group's number
    out, prev = {}, None
    for date, names in held.items():
        out[date] = 1.0 if prev is None else 1 - len(names & prev) / len(names)  # blank 4: divided by today's holdings
        prev = names
    return pd.Series(out, name="turnover", dtype=float)


def net_of_costs(gross, turnover, cost_one_way):
    t = turnover.reindex(gross.index).fillna(0.0)
    return gross - 2 * cost_one_way * t              # blank 5: you pay on the sell AND the buy


def annualised_return(period_returns, periods_per_year):
    r = period_returns.dropna()
    if r.empty:
        return 0.0
    growth = float((1 + r).prod())                     # total growth: 1.1 x 0.9 x ...
    return growth ** (periods_per_year / len(r)) - 1      # blank 6: how many periods are in r?


def sharpe(period_returns, periods_per_year):
    r = period_returns.dropna()
    sd = r.std(ddof=1)
    return float(r.mean() / sd * np.sqrt(periods_per_year)) if sd > 0 else 0.0   # blank 7


def max_drawdown(period_returns):
    equity = (1 + period_returns.fillna(0)).cumprod()                 # value of 1 yuan over time
    peak = np.maximum.accumulate(np.concatenate([[1.0], equity.values]))[1:]   # highest value so far
    return float((equity.values / peak - 1).min()) if len(equity) else 0.0      # blank 8: the WORST fall