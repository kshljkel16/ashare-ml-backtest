"""Step 4 — Walk-forward training: always train on the past, predict the future.

Test:  pytest tests/test_walkforward.py
"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

from qml.config import HORIZON, TEST_DAYS, TRAIN_DAYS


def make_splits(dates, train_days: int = TRAIN_DAYS, test_days: int = TEST_DAYS,
                gap: int = HORIZON) -> list[tuple[np.ndarray, np.ndarray]]:
    """Rolling walk-forward splits over the sorted UNIQUE dates.

    Picture, with u = sorted unique dates and `start` = index of the first test date:
        train = u[start - gap - train_days : start - gap]
        test  = u[start : start + test_days]
    The first `start` is train_days + gap; then move `start` forward by test_days
    until it runs past the end (the last test window may be shorter).

    Why the gap: the label on the last training day looks HORIZON days into the future.
    Without a gap of at least HORIZON days, training labels would contain prices from
    the test period — leakage. (This is called "purging" / an "embargo".)

    Returns a list of (train_dates, test_dates) numpy arrays.
    Hint: u = np.array(sorted(pd.unique(pd.to_datetime(pd.Series(dates)))))
    """
    raise NotImplementedError("Step 4: implement make_splits")


def default_model():
    """Provided: a deliberately small, regularised LightGBM model.

    Financial data is mostly noise. A big model memorises the noise of the training
    period and fails on the next one; few leaves, many samples per leaf and a low
    learning rate keep it simple. GUIDE.md, Step 4, explains each setting.
    """
    from lightgbm import LGBMRegressor
    return LGBMRegressor(n_estimators=200, learning_rate=0.03, num_leaves=15,
                         min_child_samples=200, subsample=0.8, subsample_freq=1,
                         colsample_bytree=0.8, random_state=0, verbose=-1)


def walk_forward_predict(df: pd.DataFrame, features: list[str], splits,
                         model_factory: Callable = default_model,
                         label: str = "fwd_ret") -> pd.DataFrame:
    """Train one fresh model per split and predict its test dates.

    Requirements (tested):
      * Drop rows with any NaN feature.
      * Target = the label's percentile rank WITHIN EACH DATE (like rank_by_date):
        the model learns "which stocks beat the others", which is what we trade.
      * For each (train_dates, test_dates):
          - training rows = rows whose date is in train_dates AND whose target is not NaN;
          - test rows     = rows whose date is in test_dates (their label may be NaN —
            predictions don't need it);
          - skip the split if either is empty;
          - model = model_factory(); model.fit(X_train, y_train); predict X_test.
      * Return ONE DataFrame with columns exactly: date, code, pred
        (out-of-sample rows only; each (date, code) once).
    Hint: df["date"].isin(train_dates) selects rows.
    """
    raise NotImplementedError("Step 4: implement walk_forward_predict")
