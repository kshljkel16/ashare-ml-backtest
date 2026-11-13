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
    u = np.array(sorted(pd.unique(pd.to_datetime(pd.Series(dates)))))   # unique trading days, in order
    splits = []
    start = train_days + gap                                   # blank 1: index of the first test day
    while start < len(u):
        train = u[start - gap - train_days : start - gap]      # blank 2: train stops this many days early
        test = u[start : start + test_days]                          # blank 3: how long is a test window?
        splits.append((train, test))
        start += test_days                                          # blank 4: slide forward by one test window
    return splits


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
    d = df.dropna(subset=features).copy()
    d["target"] = d.groupby("date")[label].rank(pct=True)          # blank 5: rank returns among stocks on the same ...?
    preds = []
    for train_dates, test_dates in splits:
        tr = d[d["date"].isin(train_dates)].dropna(subset=["target"])
        te = d[d["date"].isin(test_dates)]                             # blank 6
        if tr.empty or te.empty:
            continue
        model = model_factory()                                # a FRESH model every window
        model.fit(tr[features], tr["target"])                       # blank 7: what does the model learn to predict?
        preds.append(pd.DataFrame({"date": te["date"].values,
                                   "code": te["code"].values,
                                   "pred": model.predict(te[features])}))   # blank 8: the model's inputs
    return pd.concat(preds, ignore_index=True)