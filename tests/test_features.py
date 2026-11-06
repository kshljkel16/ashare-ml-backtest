"""Step 2."""
import numpy as np
import pandas as pd
import pytest

from qml.config import FEATURES
from qml.dataset import clean_panel
from qml.features import compute_features, rank_by_date


@pytest.fixture(scope="module")
def feats(raw):
    return compute_features(clean_panel(raw))


def test_all_features_exist(feats):
    for f in FEATURES:
        assert f in feats.columns


def test_values_on_one_stock(feats):
    s = feats[feats.code == feats.code.iloc[0]].reset_index(drop=True)
    i = 40
    assert s.loc[i, "mom_20"] == pytest.approx(s.loc[i, "close"] / s.loc[i - 20, "close"] - 1)
    assert s.loc[i, "rev_5"] == pytest.approx(-(s.loc[i, "close"] / s.loc[i - 5, "close"] - 1))
    r = s["close"].pct_change()
    assert s.loc[i, "vol_20"] == pytest.approx(r.iloc[i - 19:i + 1].std())
    assert s.loc[i, "turn_20"] == pytest.approx(s["turnover"].iloc[i - 19:i + 1].mean())
    assert s["mom_20"].iloc[:20].isna().all()             # not enough history yet


def test_no_look_ahead(raw):
    """Change everything AFTER a cut-off date: features on or before it must not move."""
    df = clean_panel(raw)
    cut = df["date"].sort_values().unique()[400]
    future = df["date"] > cut
    shocked = df.copy()
    for c in ["open", "high", "low", "close"]:
        shocked.loc[future, c] *= np.random.default_rng(0).uniform(0.5, 2.0, future.sum())
    shocked.loc[future, "turnover"] *= 3

    a = compute_features(df)
    b = compute_features(shocked)
    past_a = a[a.date <= cut].set_index(["code", "date"])[FEATURES]
    past_b = b[b.date <= cut].set_index(["code", "date"])[FEATURES]
    pd.testing.assert_frame_equal(past_a.sort_index(), past_b.sort_index())


def test_rank_by_date(feats):
    r = rank_by_date(feats, ["mom_20"])
    one_day = r[r.date == r.date.unique()[100]]["mom_20"].dropna()
    assert one_day.between(0, 1).all() and one_day.max() == 1.0
    assert feats["mom_20"].isna().sum() == r["mom_20"].isna().sum()   # NaN stays NaN
