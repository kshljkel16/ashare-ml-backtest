"""Step 3."""
import pandas as pd
import pytest

from qml.config import HORIZON
from qml.dataset import add_forward_return, clean_panel
from qml.features import compute_features
from qml.metrics import ic_summary, rank_ic_by_date


def test_rank_ic_toy():
    df = pd.DataFrame({"date": ["d1"] * 4 + ["d2"] * 4,
                       "sig": [1, 2, 3, 4, 1, 2, 3, 4],
                       "fwd_ret": [0.1, 0.2, 0.3, 0.4, 0.4, 0.3, 0.2, 0.1]})
    ic = rank_ic_by_date(df, "sig", min_stocks=3)
    assert ic.tolist() == pytest.approx([1.0, -1.0])


def test_rank_ic_skips_thin_dates_and_nans():
    df = pd.DataFrame({"date": ["d1"] * 3 + ["d2"] * 5,
                       "sig": [1, 2, 3, 1, 2, 3, 4, None],
                       "fwd_ret": [0.1, 0.2, 0.3, 0.1, 0.2, 0.3, 0.4, 0.5]})
    ic = rank_ic_by_date(df, "sig", min_stocks=4)
    assert list(ic.index) == ["d2"] and ic.iloc[0] == pytest.approx(1.0)


def test_ic_summary():
    s = ic_summary(pd.Series([0.1, 0.3, -0.1, 0.1]))
    assert s["mean"] == pytest.approx(0.1)
    assert s["icir"] == pytest.approx(0.1 / pd.Series([0.1, 0.3, -0.1, 0.1]).std())
    assert s["hit_rate"] == pytest.approx(0.75)
    assert s["n_dates"] == 4
    assert type(s["t_stat"]) is float


def test_planted_signals_are_found(raw):
    """The known-answer test: the synthetic data has momentum and reversal built in."""
    df = compute_features(add_forward_return(clean_panel(raw), HORIZON))
    assert ic_summary(rank_ic_by_date(df, "mom_20"))["mean"] > 0.01
    assert ic_summary(rank_ic_by_date(df, "rev_5"))["mean"] > 0.02
