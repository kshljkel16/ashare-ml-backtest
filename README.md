# A-share ML Backtest — cross-sectional return prediction on CSI 300

> Portfolio README — fill in the brackets with YOUR real numbers at Step 7 (see GUIDE.md).

Every week, rank CSI 300 stocks by expected 5-day return relative to each other, and test —
honestly — whether a LightGBM model beats a simple momentum rule after trading costs.

| Signal | RankIC | ICIR | Long-short Sharpe (gross) | Long-only excess, net of costs | Turnover |
|---|---|---|---|---|---|
| Momentum (20-day) | [ ] | [ ] | [ ] | [ ] | [ ] |
| LightGBM, walk-forward | [ ] | [ ] | [ ] | [ ] | [ ] |

**Key finding:** [one sentence with numbers]

## Method
- Point-in-time features (momentum, reversal, volatility, turnover, illiquidity), ranked per day.
- Label: next-open to open 5 days later (no trading at the close the signal was computed on).
- Walk-forward training (500-day window, 60-day test, purge gap = horizon).
- Evaluation on identical out-of-sample dates: RankIC, quintile returns, long-only excess after
  costs at 0/5/15/30 bp, Sharpe, max drawdown.
- A planted-signal synthetic dataset verifies the pipeline end to end.

## Limitations
[survivorship bias, cost assumption, single market/period, overlapping labels]

## Run it
```bash
pip install -e ".[dev]"
pytest -q
python -m qml.research --synthetic
python -m qml.data --start 20180101 --end 20251231
python -m qml.research
```
