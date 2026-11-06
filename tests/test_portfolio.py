"""Step 5."""
import numpy as np
import pandas as pd
import pytest

from qml.portfolio import (annualised_return, max_drawdown, net_of_costs,
                           quantile_returns, rebalance_dates, sharpe, top_quantile_turnover)


def panel():
    # 4 dates x 10 stocks; signal = stock number, return = signal / 100 -> perfect signal
    dates = pd.bdate_range("2024-01-01", periods=4)
    rows = [{"date": d, "code": f"{c:06d}", "sig": c, "fwd_ret": c / 100}
            for d in dates for c in range(10)]
    return pd.DataFrame(rows)


def test_rebalance_dates():
    d = pd.bdate_range("2024-01-01", periods=12)
    assert rebalance_dates(d, every=5) == [d[0], d[5], d[10]]


def test_quantile_returns_perfect_signal():
    q = quantile_returns(panel(), "sig", n_q=5, every=1)
    assert list(q.columns) == ["Q1", "Q2", "Q3", "Q4", "Q5"]
    assert len(q) == 4
    assert q.iloc[0].tolist() == pytest.approx([0.005, 0.025, 0.045, 0.065, 0.085])


def test_quantile_returns_uses_only_rebalance_dates():
    assert len(quantile_returns(panel(), "sig", n_q=5, every=2)) == 2


def test_turnover():
    df = panel()
    # swap the top two names out on the 3rd date
    third = df.date == df.date.unique()[2]
    df.loc[third & df.code.isin(["000008", "000009"]), "sig"] -= 100
    t = top_quantile_turnover(df, "sig", n_q=5, every=1)
    assert t.tolist() == pytest.approx([1.0, 0.0, 1.0, 1.0])


def test_net_of_costs():
    gross = pd.Series([0.01, 0.02])
    turnover = pd.Series([1.0, 0.5])
    assert net_of_costs(gross, turnover, 0.001).tolist() == pytest.approx([0.008, 0.019])


def test_sharpe_and_annualised_return():
    r = pd.Series([0.01, 0.03, 0.02, 0.0])
    assert sharpe(r, 50) == pytest.approx(r.mean() / r.std() * np.sqrt(50))
    assert annualised_return(pd.Series([0.1, 0.1]), 2) == pytest.approx(0.21)


def test_max_drawdown():
    # equity: 1.1, 0.88, 0.968, 1.1616 -> worst fall from peak 1.1 to 0.88 = -20%
    assert max_drawdown(pd.Series([0.1, -0.2, 0.1, 0.2])) == pytest.approx(-0.2)
    assert max_drawdown(pd.Series([-0.5])) == pytest.approx(-0.5)
