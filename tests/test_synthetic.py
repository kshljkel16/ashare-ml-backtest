"""Provided data — these pass from the start. Read them: they define the data contract."""
from qml.synthetic import make_panel

COLUMNS = ["date", "code", "open", "high", "low", "close", "volume", "amount", "turnover"]


def test_columns_and_types(raw):
    assert list(raw.columns) == COLUMNS
    assert raw.code.str.len().eq(6).all()


def test_deterministic():
    a = make_panel(n_stocks=5, n_days=50, seed=3)
    b = make_panel(n_stocks=5, n_days=50, seed=3)
    assert a.equals(b)


def test_suspensions_are_missing_rows(raw):
    # every stock has fewer rows than there are trading days: suspended days have no row
    per_stock = raw.groupby("code").size()
    assert (per_stock < raw.date.nunique()).mean() > 0.9
