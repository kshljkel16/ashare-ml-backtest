"""Step 4."""
import numpy as np
import pandas as pd
import pytest

from qml.config import FEATURES, HORIZON
from qml.dataset import add_forward_return, clean_panel
from qml.features import compute_features, rank_by_date
from qml.metrics import ic_summary, rank_ic_by_date
from qml.walkforward import make_splits, walk_forward_predict

DATES = pd.bdate_range("2020-01-01", periods=300)


def test_splits_shape_and_order():
    splits = make_splits(DATES, train_days=100, test_days=50, gap=5)
    assert len(splits) == 4                                # tests start at 105, 155, 205, 255
    for train, test in splits:
        assert len(train) == 100
        assert train.max() < test.min()


def test_gap_between_train_and_test():
    """The last training label looks HORIZON days ahead, so it must end before test begins."""
    u = np.array(sorted(DATES))
    for train, test in make_splits(DATES, train_days=100, test_days=50, gap=5):
        i_last_train = np.searchsorted(u, train.max())
        i_first_test = np.searchsorted(u, test.min())
        assert i_first_test - i_last_train > 5


def test_tests_do_not_overlap_and_cover_the_rest():
    splits = make_splits(DATES, train_days=100, test_days=50, gap=5)
    test_days = np.concatenate([t for _, t in splits])
    assert len(test_days) == len(set(test_days)) == 300 - 105


class MeanModel:
    """Predicts the mean of what it was trained on: lets us see exactly what it was given."""
    seen = []

    def fit(self, X, y):
        MeanModel.seen.append(len(X))
        self.m = float(np.mean(y))
        return self

    def predict(self, X):
        return np.full(len(X), self.m)


def test_predictions_are_out_of_sample_only(raw):
    df = rank_by_date(compute_features(add_forward_return(clean_panel(raw), HORIZON)), FEATURES)
    splits = make_splits(df.date, train_days=200, test_days=100, gap=HORIZON)
    MeanModel.seen = []
    preds = walk_forward_predict(df, FEATURES, splits, model_factory=MeanModel)
    test_dates = set(np.concatenate([t for _, t in splits]))
    assert set(preds.columns) == {"date", "code", "pred"}
    assert set(preds.date) <= test_dates
    assert len(MeanModel.seen) == len(splits)
    assert preds.duplicated(["date", "code"]).sum() == 0


def test_lightgbm_finds_the_planted_signal(raw):
    df = rank_by_date(compute_features(add_forward_return(clean_panel(raw), HORIZON)), FEATURES)
    splits = make_splits(df.date, train_days=250, test_days=100, gap=HORIZON)
    preds = walk_forward_predict(df, FEATURES, splits)
    merged = preds.merge(df[["date", "code", "fwd_ret"]], on=["date", "code"])
    assert ic_summary(rank_ic_by_date(merged, "pred"))["mean"] > 0.02
