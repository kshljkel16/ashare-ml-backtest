"""Step 6."""
import numpy as np
import pandas as pd
import pytest

from qml.events import abnormal_returns, align_to_trading_days, daily_event_scores, event_study

DAYS = pd.to_datetime(["2024-01-04", "2024-01-05", "2024-01-08", "2024-01-09"])   # Thu Fri Mon Tue


def test_alignment_is_conservative():
    ann = pd.DataFrame({"code": ["000001"] * 4,
                        "date": ["2024-01-05", "2024-01-06", "2024-01-08", "2024-01-03"],
                        "title": list("abcd")})
    out = align_to_trading_days(ann, DAYS)
    # trading day -> itself; Saturday -> Friday; before the first trading day -> dropped
    assert out["signal_date"].dt.strftime("%m-%d").tolist() == ["01-05", "01-05", "01-08"]
    assert out["title"].tolist() == ["a", "b", "c"]
    assert pd.api.types.is_datetime64_any_dtype(out["date"])


def test_daily_event_scores():
    labeled = pd.DataFrame({
        "code": ["000001", "000001", "000002", "000003", "000003"],
        "signal_date": pd.to_datetime(["2024-01-05"] * 5),
        "sentiment": [1, 1, -1, 0, np.nan],
    })
    out = daily_event_scores(labeled).set_index("code")
    assert out.loc["000001", "score"] == 2 and out.loc["000001", "n_ann"] == 2
    assert out.loc["000001", "group"] == "positive"
    assert out.loc["000002", "group"] == "negative"
    assert out.loc["000003", "group"] == "neutral" and out.loc["000003", "n_ann"] == 1   # NaN dropped


def panel():
    rows = []
    for code, opens in {"000001": [10, 11, 12, 13, 14], "000002": [10, 10, 10, 10, 10]}.items():
        for d, o in zip(pd.bdate_range("2024-01-01", periods=5), opens):
            rows.append({"date": d, "code": code, "open": float(o)})
    return pd.DataFrame(rows)


def test_abnormal_returns_from_next_open_minus_daily_mean():
    out = abnormal_returns(panel(), [1, 2]).set_index(["code", "date"])
    d0 = pd.Timestamp("2024-01-01")
    r1 = 12 / 11 - 1                                  # 000001: buy open day 1, sell open day 2
    assert out.loc[("000001", d0), "abn_1"] == pytest.approx(r1 - (r1 + 0) / 2)
    assert out.loc[("000002", d0), "abn_1"] == pytest.approx(0 - (r1 + 0) / 2)
    r2 = 13 / 11 - 1
    assert out.loc[("000001", d0), "abn_2"] == pytest.approx(r2 / 2)
    # each date's abnormal returns sum to zero across stocks
    sums = out.groupby(level="date")["abn_1"].sum().dropna()
    assert np.allclose(sums, 0)


def test_event_study_groups_and_stats():
    abn = pd.DataFrame({"code": ["a", "b", "c", "d", "a", "b"],
                        "date": pd.to_datetime(["2024-01-05"] * 4 + ["2024-01-08"] * 2),
                        "abn_1": [0.02, -0.01, 0.0, 0.01, 0.04, -0.03]})
    events = pd.DataFrame({"code": ["a", "b", "a"],
                           "signal_date": pd.to_datetime(["2024-01-05", "2024-01-05", "2024-01-08"]),
                           "group": ["positive", "negative", "positive"]})
    t = event_study(abn, events, [1]).set_index("group")
    assert set(t.index) == {"positive", "negative", "no_news"}
    assert t.loc["positive", "n"] == 2 and t.loc["positive", "mean"] == pytest.approx(0.03)
    assert t.loc["no_news", "n"] == 3 and t.loc["no_news", "mean"] == pytest.approx(-0.02 / 3)
    x = pd.Series([0.02, 0.04])
    assert t.loc["positive", "t_stat"] == pytest.approx(x.mean() / x.std() * np.sqrt(2))
