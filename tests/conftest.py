import pytest

from qml.synthetic import make_panel


@pytest.fixture(scope="session")
def raw():
    """Synthetic panel with planted momentum and reversal (see qml/synthetic.py)."""
    return make_panel(n_stocks=80, n_days=700, seed=1)
