"""Step 5 — From signal to portfolio: quintiles, turnover, costs, Sharpe, drawdown.

Test:  pytest tests/test_portfolio.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from qml.config import N_QUANTILES, REBALANCE_EVERY


def rebalance_dates(dates, every: int = REBALANCE_EVERY) -> list:
    """Every `every`-th sorted unique date, starting with the first: [d0, d5, d10, ...].

    Why: the label is a 5-day return. Rebalancing every 5 days makes holding periods
    back-to-back without overlap, so each day's return is counted once.
    """
    raise NotImplementedError("Step 5: implement rebalance_dates")


def quantile_returns(df: pd.DataFrame, signal: str, label: str = "fwd_ret",
                     n_q: int = N_QUANTILES, every: int = REBALANCE_EVERY) -> pd.DataFrame:
    """Average `label` of each signal quintile, on each rebalance date.

    Requirements (tested):
      * Keep rows with both signal and label, on rebalance dates only.
      * On each date, split stocks into n_q equal groups by signal: Q1 = lowest, Qn = highest.
        Use pd.qcut(s.rank(method="first"), n_q, labels=False) + 1 — ranking first
        breaks ties, so the groups are always equal-sized.
      * Return a DataFrame: index = date, columns "Q1".."Qn", values = mean label.
    """
    raise NotImplementedError("Step 5: implement quantile_returns")


def top_quantile_turnover(df: pd.DataFrame, signal: str, n_q: int = N_QUANTILES,
                          every: int = REBALANCE_EVERY) -> pd.Series:
    """Share of the TOP quintile that is replaced at each rebalance.

    On each rebalance date, find the set of codes in the top quintile (same qcut as
    above). turnover = 1 - |held today ∩ held last time| / |held today|.
    The first date is 1.0 (you buy everything). Returns a Series indexed by date.
    """
    raise NotImplementedError("Step 5: implement top_quantile_turnover")


def net_of_costs(gross: pd.Series, turnover: pd.Series, cost_one_way: float) -> pd.Series:
    """Period returns after trading costs.

    Replacing a share `turnover` of the portfolio means selling that share AND buying
    its replacement, so the cost is 2 * cost_one_way * turnover.
    Align turnover to gross's index; a missing turnover counts as 0.
    """
    raise NotImplementedError("Step 5: implement net_of_costs")


def annualised_return(period_returns: pd.Series, periods_per_year: float) -> float:
    """Compound growth per year: (prod(1 + r)) ** (periods_per_year / n) - 1.
    Ignore NaN; an empty series gives 0.0.
    """
    raise NotImplementedError("Step 5: implement annualised_return")


def sharpe(period_returns: pd.Series, periods_per_year: float) -> float:
    """Annualised Sharpe ratio (risk-free rate taken as 0):
    mean / std (ddof=1) * sqrt(periods_per_year). Ignore NaN; std 0 gives 0.0.
    """
    raise NotImplementedError("Step 5: implement sharpe")


def max_drawdown(period_returns: pd.Series) -> float:
    """Worst fall from a previous peak of the equity curve, as a negative fraction.

    equity = cumulative product of (1 + r), starting from 1.0 BEFORE the first period
    (so a first-period loss counts). drawdown = equity / running peak - 1; return its min.
    Example: returns +10%, -20% -> equity 1.10, 0.88 -> max drawdown -20%.
    """
    raise NotImplementedError("Step 5: implement max_drawdown")
