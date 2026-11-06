"""Step 1."""
import numpy as np
import pandas as pd
import pytest

from qml.dataset import add_forward_return, clean_panel


def toy():
    return pd.DataFrame({
        "date": ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05", "2024-01-08", "2024-01-03"],
        "code": [1, 1, 1, 1, 1, "000002"],
        "open":  [10.0, 11.0, 12.0, 13.0, 14.0, 5.0],
        "high":  [10.5, 11.5, 12.5, 13.5, 14.5, 5.5],
        "low":   [9.5, 10.5, 11.5, 12.5, 13.5, 4.5],
        "close": [10.2, 11.2, 12.2, 13.2, 14.2, 5.2],
        "volume": [100, 100, 100, 100, 100, 0],
        "amount": [1e3] * 6,
        "turnover": [1.0] * 6,
    })


def test_clean_types_sort_and_filters():
    out = clean_panel(toy())
    assert pd.api.types.is_datetime64_any_dtype(out["date"])
    assert set(out["code"]) == {"000001"}                 # zero-padded; zero-volume row dropped
    assert out["date"].is_monotonic_increasing
    assert out.index.tolist() == list(range(len(out)))


def test_clean_removes_duplicates():
    df = pd.concat([toy(), toy().iloc[[0]]])
    out = clean_panel(df)
    assert not out.duplicated(["code", "date"]).any()


def test_forward_return_is_next_open_to_open():
    out = add_forward_return(clean_panel(toy()), horizon=2)
    # signal at the close of day 0 -> buy at day 1 open (11) -> sell at day 3 open (13)
    assert out.loc[0, "fwd_ret"] == pytest.approx(13 / 11 - 1)
    assert out.loc[1, "fwd_ret"] == pytest.approx(14 / 12 - 1)
    assert out["fwd_ret"].iloc[2:].isna().all()           # not enough future: NaN, never filled


def test_forward_return_never_crosses_stocks(raw):
    out = add_forward_return(clean_panel(raw), horizon=5)
    last_rows = out.groupby("code").tail(5)
    assert last_rows["fwd_ret"].isna().all()
